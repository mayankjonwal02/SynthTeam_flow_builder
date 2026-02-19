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
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from app.db.session import AsyncSessionLocal
from app.models.models import WorkflowExecutionLog

logger = logging.getLogger("uvicorn.error")

_ACTIVE_ROUTES: Dict[str, dict] = {}


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
    method = plan["method"]
    RequestModel  = plan.get("request_model")
    ResponseModel = plan.get("response_model")
    QueryModel    = plan.get("query_model")
    rate_limit    = plan.get("rate_limit")

    _workflow_id = workflow_id

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

    # Remove old route at the same path if re-deploying
    app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != path]

    app.add_api_route(path, endpoint_handler, **kwargs)

    app.openapi_schema = None

    _ACTIVE_ROUTES[path] = {"method": method, "tag": tag}
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

    from app.utils.rate_limiter import check_rate_limit

    api_key = request.headers.get("x-api-key", request.client.host if request.client else "anon")
    limit_key = f"ratelimit:{api_key}:{request.url.path}"
    await check_rate_limit(
        redis_client,
        limit_key,
        rate_limit.get("requests", 100),
        rate_limit.get("window_seconds", 60),
    )


async def _handle_result(
    execution: dict,
    workflow_id: Optional[_uuid.UUID],
    debug: bool,
) -> Any:
    """Persist execution log and return the appropriate response."""
    trace  = execution.get("trace", [])
    result = execution.get("result")
    exec_id = _uuid.uuid4()

    has_failure = any(
        entry.get("status") == "failed" for entry in trace
    )
    status = "failed" if has_failure else "success"

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

    return result


def unregister_route(app: FastAPI, path: str):
    """Remove a dynamically deployed route and its cron job if any."""
    app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != path]
    _ACTIVE_ROUTES.pop(path, None)
    app.openapi_schema = None
    logger.info(f"Undeployed route: {path}")

    try:
        from app.scheduler import remove_cron_job
        for key in list(_ACTIVE_ROUTES.keys()):
            pass
        remove_cron_job(f"cron_{path}")
    except Exception:
        pass


def list_routes() -> dict:
    """Return all currently active deployed routes."""
    return dict(_ACTIVE_ROUTES)
