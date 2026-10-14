from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.models import File, Project
from app.api.deps import get_owned_project, require_fields
from app.runtime.deployment import delete_file_and_logs
from app.core.auth import verify_token
import uuid
import copy

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ===================== CREATE =====================
@router.post("")
async def create_project(data: dict, user=Depends(verify_token)):
    require_fields(data, "name")
    async with AsyncSessionLocal() as session:
        p = Project(
            id=uuid.uuid4(),
            user_id=user["sub"],
            name=str(data["name"]).strip()
        )
        session.add(p)
        await session.commit()
        await session.refresh(p)

        return {
            "id": str(p.id),
            "name": p.name
        }


# ===================== READ =====================
@router.get("")
async def get_projects(user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Project).where(Project.user_id == user["sub"])
        )

        projects = res.scalars().all()

        return [
            {"id": str(p.id), "name": p.name}
            for p in projects
        ]


# ===================== UPDATE =====================
@router.put("/{project_id}")
async def update_project(project_id: str, data: dict, user=Depends(verify_token)):
    require_fields(data, "name")
    async with AsyncSessionLocal() as session:
        p = await get_owned_project(session, project_id, user)
        p.name = str(data["name"]).strip()
        await session.commit()

        return {"success": True}


# ===================== DELETE =====================
@router.delete("/{project_id}")
async def delete_project(project_id: str, request: Request, user=Depends(verify_token)):
    async with AsyncSessionLocal() as session:
        p = await get_owned_project(session, project_id, user)

        res = await session.execute(select(File).where(File.project_id == p.id))
        for f in res.scalars().all():
            await delete_file_and_logs(session, request.app, f)

        await session.delete(p)
        await session.commit()

        return {"success": True}


# ===================== OPENAPI (per-project) =====================
@router.get("/{project_id}/openapi")
async def get_project_openapi(project_id: str, request: Request, user=Depends(verify_token)):
    """
    Returns an OpenAPI 3.1 JSON document containing only the
    routes that belong to this project (matched by the project
    name tag assigned at deploy time).
    """
    async with AsyncSessionLocal() as session:
        project = await get_owned_project(session, project_id, user)

    # Tag format: projectname_projectid (same as deploy-time tag)
    tag = f"{project.name}_{project.id}"

    # Get the full OpenAPI schema from FastAPI
    full_schema = request.app.openapi()
    if not full_schema:
        return {"openapi": "3.1.0", "info": {"title": tag, "version": "1.0.0"}, "paths": {}}

    filtered_schema = copy.deepcopy(full_schema)

    # Override info to be project-specific
    filtered_schema["info"] = {
        "title": f"{project.name} — API",
        "version": "1.0.0",
        "description": f"Auto-generated OpenAPI spec for the \"{project.name}\" project namespace ({project.id}).",
    }

    # Filter paths: keep only operations whose tags include the project name
    filtered_paths = {}
    for path, methods in full_schema.get("paths", {}).items():
        filtered_methods = {}
        for method, operation in methods.items():
            if method.startswith("x-"):
                continue
            op_tags = operation.get("tags", [])
            if tag in op_tags:
                filtered_methods[method] = operation
        if filtered_methods:
            filtered_paths[path] = filtered_methods

    filtered_schema["paths"] = filtered_paths

    # Collect only the $ref schemas that are actually used
    used_refs = set()
    schema_json = str(filtered_paths)
    import re
    for ref_match in re.findall(r'#/components/schemas/(\w+)', schema_json):
        used_refs.add(ref_match)

    if "components" in filtered_schema and "schemas" in filtered_schema["components"]:
        all_schemas = filtered_schema["components"]["schemas"]
        # Keep only referenced schemas (plus any they reference transitively)
        kept = {}
        to_check = list(used_refs)
        while to_check:
            name = to_check.pop()
            if name in kept or name not in all_schemas:
                continue
            kept[name] = all_schemas[name]
            # Check for nested refs
            nested = re.findall(r'#/components/schemas/(\w+)', str(all_schemas[name]))
            to_check.extend(nested)
        filtered_schema["components"]["schemas"] = kept

    # Remove tags list except for this project's tag
    filtered_schema["tags"] = [{"name": tag}]

    return filtered_schema
