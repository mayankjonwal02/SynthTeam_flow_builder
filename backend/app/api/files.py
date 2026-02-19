from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.models import File, Project, WorkflowExecutionLog
from app.core.auth import verify_token
import uuid
from app.runtime.compiler import GraphCompiler
from app.runtime.executor import GraphExecutor
from app.runtime.registry import register_route, unregister_route


router = APIRouter(prefix="/api/files", tags=["files"])


# CREATE file under project
@router.post("")
async def create_file(data: dict, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        f = File(
            id=uuid.uuid4(),
            project_id=data["project_id"],
            name=data["name"],
            graph_json={"nodes": [], "edges": []}
        )
        session.add(f)
        await session.commit()
        return {"id": str(f.id), "name": f.name}


# READ files under project  (includes deploy status)
@router.get("/project/{project_id}")
async def get_files(project_id: str, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(File).where(File.project_id == project_id)
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
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")
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
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(WorkflowExecutionLog)
            .where(WorkflowExecutionLog.workflow_id == file_id)
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
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")
        return f.graph_json


# UPDATE specific file (graph json)
@router.put("/{file_id}")
async def update_file(file_id: str, data: dict, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")
        f.graph_json = data["graph"]
        await session.commit()
        return {"success": True}


# DELETE file
@router.delete("/{file_id}")
async def delete_file(file_id: str, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")
        await session.delete(f)
        await session.commit()
        return {"success": True}


# ── DEPLOY ─────────────────────────────────────────────────────────
@router.post("/deploy/{file_id}")
async def deploy_file(file_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")

        # Fetch project name for OpenAPI tag / namespace
        proj_res = await session.execute(
            select(Project).where(Project.id == f.project_id)
        )
        project = proj_res.scalar()
        tag = f"{project.name}_{project.id}" if project else "deployed"

        graph = f.graph_json
        compiler = GraphCompiler(graph)
        plan = compiler.compile()
        executor = GraphExecutor(plan)

        register_route(request.app, plan, executor, tag=tag, workflow_id=f.id)

        # Persist deploy state
        f.is_deployed = True
        f.deployed_path = plan["path"]
        f.deployed_method = plan["method"]
        await session.commit()

        return {
            "success": True,
            "endpoint": plan["path"],
            "method": plan["method"],
            "tag": tag,
        }


# ── UNDEPLOY ───────────────────────────────────────────────────────
@router.post("/undeploy/{file_id}")
async def undeploy_file(file_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar()
        if not f:
            raise HTTPException(status_code=404, detail="File not found")
        if not f.is_deployed:
            raise HTTPException(status_code=400, detail="Flow is not deployed")

        # Remove the live route
        unregister_route(request.app, f.deployed_path)

        old_path = f.deployed_path
        f.is_deployed = False
        f.deployed_path = None
        f.deployed_method = None
        await session.commit()

        return {"success": True, "removed": old_path}