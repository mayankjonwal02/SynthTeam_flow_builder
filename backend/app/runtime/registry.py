"""
Route Registry — dynamically adds/removes endpoints on the running FastAPI app.

Handles:
  - Dynamic route registration with optional response model
  - Query parameter and path parameter support
  - Header injection into request_data
  - Rate limiting (via Redis sliding window)
  - Execution log persistence (WorkflowExecutionLog)
  - Debug mode (?debug=true returns full execution trace)
  - Cron job scheduling hooks

Component registry lives in app.components.component_registry.
"""

import uuid as _uuid
import logging
from datetime import datetime, date
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from app.db.session import AsyncSessionLocal
from app.models.models import WorkflowExecutionLog

logger = logging.getLogger("uvicorn.error")


def _json_serialize(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types to serializable ones."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, _uuid.UUID):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: _json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serialize(item) for item in obj]
    return obj

# key -> {"path", "method", "tag", "route", "workflow_id"}
# key is the workflow id (or "path:<path>" for routes registered without one)
_ACTIVE_ROUTES: Dict[str, dict] = {}

# Deployed workflows may not live under these prefixes (platform API, docs, websockets)
RESERVED_PREFIXES = ("/api", "/agent", "/ws", "/docs", "/redoc", "/openapi.json")
RESERVED_PATHS = ("/", "/protected")

_SENSITIVE_HEADERS = frozenset({
    "authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key",
})


class DeployError(ValueError):
    """A workflow can't be deployed at the requested path."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def _route_key(workflow_id: Optional[_uuid.UUID], path: str) -> str:
    return str(workflow_id) if workflow_id is not None else f"path:{path}"


def validate_deploy_path(path: str) -> None:
    """Reject paths that would shadow platform routes."""
    if not isinstance(path, str) or not path.startswith("/"):
        raise DeployError("Endpoint path must start with '/'")
    normalized = path.rstrip("/") or "/"
    if normalized in RESERVED_PATHS:
        raise DeployError(f"Path {path!r} is reserved")
    for prefix in RESERVED_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + "/") or normalized.startswith(prefix + "."):
            raise DeployError(f"Paths under {prefix!r} are reserved for the SynthTeam API")


def _check_conflicts(app: FastAPI, key: str, path: str, method: str) -> None:
    managed = {id(info["route"]) for info in _ACTIVE_ROUTES.values()}
    for other_key, info in _ACTIVE_ROUTES.items():
        if other_key != key and info["path"] == path and info["method"] == method:
            raise DeployError(
                f"{method} {path} is already used by another deployed workflow",
                status_code=409,
            )
    for route in app.routes:
        if id(route) in managed:
            continue
        if getattr(route, "path", None) == path:
            raise DeployError(f"Path {path!r} is used by the SynthTeam API")


def redact_headers(obj: Any) -> Any:
    """Recursively mask credential headers inside any __headers__ dicts."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "__headers__" and isinstance(v, dict):
                out[k] = {
                    hk: ("[redacted]" if str(hk).lower() in _SENSITIVE_HEADERS else hv)
                    for hk, hv in v.items()
                }
            else:
                out[k] = redact_headers(v)
        return out
    if isinstance(obj, list):
        return [redact_headers(v) for v in obj]
    return obj


def register_route(
    app: FastAPI,
    plan: dict,
    executor,
    *,
    tag: str = "deployed",
    workflow_id: Optional[_uuid.UUID] = None,
):
    """Register a compiled workflow as a live FastAPI route."""
    path   = plan["path"]
    method = str(plan["method"]).upper()
    RequestModel  = plan.get("request_model")
    ResponseModel = plan.get("response_model")
    QueryModel    = plan.get("query_model")
    rate_limit    = plan.get("rate_limit")

    _workflow_id = workflow_id
    key = _route_key(workflow_id, path)

    validate_deploy_path(path)
    _check_conflicts(app, key, path, method)

    # ── build the endpoint handler dynamically ──────────────────────
    if RequestModel and QueryModel:
        async def endpoint_handler(
            request: Request,
            body: RequestModel,                     # type: ignore[valid-type]
            query: QueryModel = Query(None),        # type: ignore[valid-type]
            debug: bool = Query(False),
        ):
            request_data = body.model_dump()
            request_data["__headers__"] = dict(request.headers)
            if query:
                request_data["__query__"] = query.model_dump() if hasattr(query, "model_dump") else {}
            request_data["__path_params__"] = request.path_params
            if rate_limit:
                await _enforce_rate_limit(request, rate_limit)
            execution = await executor.execute(request_data)
            return await _handle_result(execution, _workflow_id, debug)

    elif RequestModel:
        async def endpoint_handler(
            request: Request,
            body: RequestModel,                     # type: ignore[valid-type]
            debug: bool = Query(False),
        ):
            request_data = body.model_dump()
            request_data["__headers__"] = dict(request.headers)
            request_data["__path_params__"] = request.path_params
            if rate_limit:
                await _enforce_rate_limit(request, rate_limit)
            execution = await executor.execute(request_data)
            return await _handle_result(execution, _workflow_id, debug)

    elif QueryModel:
        async def endpoint_handler(
            request: Request,
            query: QueryModel = Query(None),        # type: ignore[valid-type]
            debug: bool = Query(False),
        ):
            request_data: dict = {}
            request_data["__headers__"] = dict(request.headers)
            if query:
                request_data["__query__"] = query.model_dump() if hasattr(query, "model_dump") else {}
            request_data["__path_params__"] = request.path_params
            if rate_limit:
                await _enforce_rate_limit(request, rate_limit)
            execution = await executor.execute(request_data)
            return await _handle_result(execution, _workflow_id, debug)

    else:
        async def endpoint_handler(
            request: Request,
            debug: bool = Query(False),
        ):
            request_data: dict = {}
            request_data["__headers__"] = dict(request.headers)
            request_data["__path_params__"] = request.path_params
            if rate_limit:
                await _enforce_rate_limit(request, rate_limit)
            execution = await executor.execute(request_data)
            return await _handle_result(execution, _workflow_id, debug)

    kwargs: dict = {"methods": [method], "tags": [tag]}
    if ResponseModel:
        kwargs["response_model"] = ResponseModel

    # Re-deploying replaces only this workflow's previous route (whatever its path)
    _remove_route(app, key)

    app.add_api_route(path, endpoint_handler, **kwargs)
    route = app.routes[-1]

    app.openapi_schema = None

    _ACTIVE_ROUTES[key] = {
        "path": path, "method": method, "tag": tag,
        "route": route, "workflow_id": workflow_id,
    }
    logger.info(f"Deployed route: {method} {path}  [tag={tag}]")

    # ── cron scheduling ─────────────────────────────────────────────
    if plan.get("has_cron") and plan.get("cron_expression"):
        try:
            from app.scheduler import add_cron_job

            async def _cron_callback():
                execution = await executor.execute({})
                await _handle_result(execution, _workflow_id, debug=False)

            job_id = f"cron_{workflow_id}" if workflow_id else f"cron_{path}"
            add_cron_job(job_id, plan["cron_expression"], _cron_callback)
            logger.info(f"Scheduled cron job: {job_id} [{plan['cron_expression']}]")
        except Exception as exc:
            logger.warning(f"Could not schedule cron job: {exc}")


async def _enforce_rate_limit(request: Request, rate_limit: dict):
    """Check rate limit using Redis if available on app.state."""
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        return

    from fastapi import HTTPException
    from app.utils.rate_limiter import check_rate_limit

    # Key on the client address; a caller-supplied header would let anyone
    # dodge the limit by sending a new value each time.
    client = request.client.host if request.client else "anon"
    limit_key = f"ratelimit:{client}:{request.url.path}"
    try:
        await check_rate_limit(
            redis_client,
            limit_key,
            int(rate_limit.get("requests", 100)),
            int(rate_limit.get("window_seconds", 60)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rate limiting skipped (Redis unavailable): {exc}")


async def _handle_result(
    execution: dict,
    workflow_id: Optional[_uuid.UUID],
    debug: bool,
) -> Any:
    """Persist execution log and return the appropriate response."""
    trace  = redact_headers(_json_serialize(execution.get("trace", [])))
    result = redact_headers(_json_serialize(execution.get("result")))
    halted = execution.get("halted")
    exec_id = _uuid.uuid4()

    failed_nodes = [
        {"node": entry.get("node_name"), "error": entry.get("error")}
        for entry in trace if entry.get("status") == "failed"
    ]
    if halted:
        status = "rejected"
    elif failed_nodes:
        status = "failed"
    else:
        status = "success"

    if workflow_id is not None:
        try:
            async with AsyncSessionLocal() as session:
                log = WorkflowExecutionLog(
                    workflow_id=workflow_id,
                    execution_id=exec_id,
                    status=status,
                    trace=trace,
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            logger.error(f"Failed to persist execution log: {exc}")

    if debug:
        return JSONResponse(content={
            "execution_id": str(exec_id),
            "status": status,
            "result": result,
            "trace": trace,
        })

    if halted:
        # A node (e.g. Auth Gate) rejected the request: stop with its status
        return JSONResponse(
            status_code=halted["status_code"],
            content={"detail": halted["detail"]},
        )
    if failed_nodes:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Workflow execution failed",
                "execution_id": str(exec_id),
                "failed_nodes": failed_nodes,
            },
        )

    return result


def _remove_route(app: FastAPI, key: str) -> Optional[dict]:
    info = _ACTIVE_ROUTES.pop(key, None)
    if not info:
        return None
    app.routes[:] = [r for r in app.routes if r is not info["route"]]
    app.openapi_schema = None
    try:
        from app.scheduler import remove_cron_job
        wid = info.get("workflow_id")
        remove_cron_job(f"cron_{wid}" if wid else f"cron_{info['path']}")
    except Exception:
        pass
    return info


def unregister_route(app: FastAPI, workflow_id: Optional[_uuid.UUID] = None, path: Optional[str] = None):
    """Remove a workflow's deployed route and its cron job, if any."""
    key = _route_key(workflow_id, path or "")
    info = _remove_route(app, key)
    if info:
        logger.info(f"Undeployed route: {info['method']} {info['path']}")


def list_routes() -> dict:
    """Return all currently active deployed routes."""
    return {
        info["path"]: {"method": info["method"], "tag": info["tag"]}
        for info in _ACTIVE_ROUTES.values()
    }
