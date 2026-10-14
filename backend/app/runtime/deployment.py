"""
Deploy / undeploy workflow files and restore deployed routes on startup.

Used by the files API and by app startup so both register routes the same way.
"""

import logging

from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.models.models import File, Project
from app.runtime.compiler import GraphCompiler
from app.runtime.executor import GraphExecutor
from app.runtime.registry import DeployError, register_route, unregister_route

logger = logging.getLogger("uvicorn.error")


def project_tag(project: Project) -> str:
    """OpenAPI tag grouping a project's routes (format relied on by /openapi)."""
    return f"{project.name}_{project.id}"


def deploy_file(app: FastAPI, f: File, project: Project) -> dict:
    """
    Compile a file's graph and mount it as a live route.

    Raises DeployError / HTTPException from the compiler or registry on failure.
    Updates the file's deploy fields; the caller commits.
    """
    plan = GraphCompiler(f.graph_json or {}).compile()
    # Lets DB nodes check that stored connections belong to the flow's owner
    plan["owner_id"] = project.user_id
    tag = project_tag(project)
    register_route(app, plan, GraphExecutor(plan), tag=tag, workflow_id=f.id)

    f.is_deployed = True
    f.deployed_path = plan["path"]
    f.deployed_method = str(plan["method"]).upper()
    return {"endpoint": plan["path"], "method": f.deployed_method, "tag": tag}


def undeploy_file(app: FastAPI, f: File) -> None:
    unregister_route(app, workflow_id=f.id, path=f.deployed_path)
    f.is_deployed = False
    f.deployed_path = None
    f.deployed_method = None


async def restore_deployed_routes(app: FastAPI) -> None:
    """Re-register every file marked as deployed (routes live in memory only)."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(File, Project)
            .join(Project, File.project_id == Project.id)
            .where(File.is_deployed.is_(True))
        )
        restored, failed = 0, 0
        for f, project in res.all():
            try:
                deploy_file(app, f, project)
                restored += 1
            except (DeployError, HTTPException) as exc:
                # The saved graph no longer compiles or its path is invalid/taken:
                # mark it undeployed so the UI doesn't claim it's live.
                detail = getattr(exc, "detail", None) or str(exc)
                logger.error(f"Undeploying workflow {f.id} ({f.name}): {detail}")
                f.is_deployed = False
                f.deployed_path = None
                f.deployed_method = None
                failed += 1
            except Exception as exc:
                # Possibly transient (e.g. a provider import failed): keep the flag
                logger.error(f"Could not restore deployed workflow {f.id} ({f.name}): {exc}")
                failed += 1
        await session.commit()
    logger.info(f"Restored {restored} deployed workflow(s); {failed} could not be restored.")


async def delete_file_and_logs(session: AsyncSession, app: FastAPI, f: File) -> None:
    """Undeploy a file, delete its execution logs, then the file (caller commits)."""
    from sqlalchemy import delete

    from app.models.models import WorkflowExecutionLog

    if f.is_deployed:
        unregister_route(app, workflow_id=f.id, path=f.deployed_path)
    await session.execute(
        delete(WorkflowExecutionLog).where(WorkflowExecutionLog.workflow_id == f.id)
    )
    await session.delete(f)
