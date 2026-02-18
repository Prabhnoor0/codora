"""Graph router — knowledge graph queries and visualization."""
from fastapi import APIRouter, Depends, HTTPException

from routers.deps import get_current_user
from services.graph_service import get_graph_service

router = APIRouter()


@router.get("/repo/{owner}/{repo_name}/architecture")
async def get_repo_graph(owner: str, repo_name: str, current_user=Depends(get_current_user)):
    """Get repository code graph structure."""
    from sqlalchemy import select
    from database import get_db
    # This is simplified — in production we'd get the repo_id from DB
    graph = get_graph_service()
    return await graph.get_repo_architecture(f"{owner}_{repo_name}")


@router.get("/developer")
async def get_developer_graph(current_user=Depends(get_current_user)):
    """Get full developer knowledge graph for 3D visualization."""
    graph = get_graph_service()
    data = await graph.get_developer_knowledge_graph(current_user.github_id)
    return data


@router.get("/repo/{owner}/{repo_name}/file-connections")
async def get_file_connections(
    owner: str,
    repo_name: str,
    path: str,
    current_user=Depends(get_current_user),
):
    """Get files connected to a specific file via imports."""
    # Get repo_id first
    from sqlalchemy import select
    from database import AsyncSessionLocal
    from models.repository import Repository

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
        )
        repo = result.scalar_one_or_none()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet")

    graph = get_graph_service()
    related = await graph.get_related_files(str(repo.id), path)
    return {"file": path, "connected_files": related}
