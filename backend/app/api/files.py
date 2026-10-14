from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.models import File, WorkflowExecutionLog
from app.core.auth import verify_token
from app.api.deps import get_owned_file, get_owned_project, require_fields
from app.runtime.deployment import delete_file_and_logs, deploy_file, undeploy_file
from app.runtime.registry import DeployError
import uuid


router = APIRouter(prefix="/api/files", tags=["files"])


# CREATE file under project
@router.post("")
async def create_file(data: dict, user=Depends(verify_token)):
    require_fields(data, "project_id", "name")
    async with AsyncSessionLocal() as session:
        project = await get_owned_project(session, data["project_id"], user)
        f = File(
            id=uuid.uuid4(),
            project_id=project.id,
            name=str(data["name"]).strip(),
            graph_json={"nodes": [], "edges": []}
        )
        session.add(f)
        await session.commit()
        return {"id": str(f.id), "name": f.name}


# READ files under project  (includes deploy status)
@router.get("/project/{project_id}")
async def get_files(project_id: str, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        project = await get_owned_project(session, project_id, user)
        res = await session.execute(
            select(File).where(File.project_id == project.id)
        )
        return [
            {
                "id": str(f.id),
                "name": f.name,
                "is_deployed": f.is_deployed or False,
                "deployed_path": f.deployed_path,
                "deployed_method": f.deployed_method,
            }
            for f in res.scalars().all()
        ]


# READ file metadata  (graph + deploy status)
@router.get("/{file_id}/meta")
async def get_file_meta(file_id: str, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        return {
            "id": str(f.id),
            "name": f.name,
            "is_deployed": f.is_deployed or False,
            "deployed_path": f.deployed_path,
            "deployed_method": f.deployed_method,
        }


# READ execution logs for a workflow
@router.get("/{file_id}/logs")
async def get_execution_logs(file_id: str, limit: int = 50, user=Depends(verify_token)):
    limit = max(1, min(limit, 500))
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        res = await session.execute(
            select(WorkflowExecutionLog)
            .where(WorkflowExecutionLog.workflow_id == f.id)
            .order_by(WorkflowExecutionLog.created_at.desc())
            .limit(limit)
        )
        logs = res.scalars().all()
        return [
            {
                "id": str(log.id),
                "execution_id": str(log.execution_id),
                "status": log.status,
                "trace": log.trace,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]


# READ specific file (graph json)
@router.get("/{file_id}")
async def get_file(file_id: str, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        return f.graph_json


# UPDATE specific file (graph json)
@router.put("/{file_id}")
async def update_file(file_id: str, data: dict, user=Depends(verify_token)):
    graph = data.get("graph")
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes", []), list):
        raise HTTPException(status_code=422, detail="Body must be {\"graph\": {\"nodes\": [...], \"edges\": [...]}}")
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        f.graph_json = graph
        await session.commit()
        return {"success": True}


# DELETE file
@router.delete("/{file_id}")
async def delete_file(file_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        await delete_file_and_logs(session, request.app, f)
        await session.commit()
        return {"success": True}


# ── DEPLOY ─────────────────────────────────────────────────────────
@router.post("/deploy/{file_id}")
async def deploy_file_route(file_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f, project = await get_owned_file(session, file_id, user)
        try:
            info = deploy_file(request.app, f, project)
        except DeployError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc))
        await session.commit()

        return {"success": True, **info}


# ── UNDEPLOY ───────────────────────────────────────────────────────
@router.post("/undeploy/{file_id}")
async def undeploy_file_route(file_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f, _ = await get_owned_file(session, file_id, user)
        if not f.is_deployed:
            raise HTTPException(status_code=400, detail="Flow is not deployed")

        old_path = f.deployed_path
        undeploy_file(request.app, f)
        await session.commit()

        return {"success": True, "removed": old_path}
