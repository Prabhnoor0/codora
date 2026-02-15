"""Repositories router — analysis, summary, architecture."""
import re
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from database import get_db
from models.repository import Repository, AnalysisStatus
from routers.deps import get_current_user
from services.github_service import GitHubService
from tasks.analyze_repo import full_analysis

router = APIRouter()
log = structlog.get_logger()


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    patterns = [
        r"github\.com[:/]([^/]+)/([^/.\s]+?)(?:\.git)?$",
        r"^([^/]+)/([^/]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"Cannot parse GitHub URL: {url}")


@router.post("/analyze")
async def analyze_repository(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit a repository URL for analysis."""
    repo_url = payload.get("url", "")
    try:
        owner, repo_name = parse_github_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    full_name = f"{owner}/{repo_name}"

    # Check if already analyzed recently
    result = await db.execute(select(Repository).where(Repository.full_name == full_name))
    repo = result.scalar_one_or_none()

    if repo and repo.analysis_status == AnalysisStatus.COMPLETED:
        return {"status": "cached", "repo_id": str(repo.id), "full_name": full_name}

    # Fetch basic repo info from GitHub
    github = GitHubService(current_user.github_access_token)
    try:
        repo_data = await github.get_repo(owner, repo_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Repository not found: {e}")

    if not repo:
        repo = Repository(
            github_id=repo_data["id"],
            full_name=full_name,
            owner=owner,
            name=repo_name,
            description=repo_data.get("description"),
            url=repo_data.get("html_url", ""),
            default_branch=repo_data.get("default_branch", "main"),
            language=repo_data.get("language"),
            topics=repo_data.get("topics", []),
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            open_issues_count=repo_data.get("open_issues_count", 0),
            license=repo_data.get("license", {}).get("spdx_id") if repo_data.get("license") else None,
            analysis_status=AnalysisStatus.PENDING,
        )
        db.add(repo)
        await db.flush()
    else:
        repo.analysis_status = AnalysisStatus.PENDING
        repo.analysis_progress = 0

    await db.commit()
    await db.refresh(repo)

    # Launch Celery task
    task = full_analysis.delay(
        str(repo.id), owner, repo_name, current_user.github_access_token
    )

    return {
        "status": "started",
        "repo_id": str(repo.id),
        "task_id": task.id,
        "full_name": full_name,
    }


@router.get("/{owner}/{repo_name}")
async def get_repository(
    owner: str,
    repo_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get full repository analysis data."""
    full_name = f"{owner}/{repo_name}"
    result = await db.execute(select(Repository).where(Repository.full_name == full_name))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found. Submit for analysis first.")

    return {
        "id": str(repo.id),
        "full_name": repo.full_name,
        "owner": repo.owner,
        "name": repo.name,
        "description": repo.description,
        "url": repo.url,
        "stars": repo.stars,
        "forks": repo.forks,
        "language": repo.language,
        "topics": repo.topics,
        "analysis_status": repo.analysis_status,
        "analysis_progress": repo.analysis_progress,
        "analysis_stage": repo.analysis_stage,
        "purpose": repo.purpose,
        "tech_stack": repo.tech_stack,
        "architecture_summary": repo.architecture_summary,
        "main_modules": repo.main_modules,
        "subsystems": repo.subsystems,
        "architecture_diagram": repo.architecture_diagram,
        "difficulty_level": repo.difficulty_level,
        "contribution_areas": repo.contribution_areas,
        "learning_prerequisites": repo.learning_prerequisites,
        "embeddings_indexed": repo.embeddings_indexed,
        "graph_built": repo.graph_built,
        "last_analyzed": repo.last_analyzed.isoformat() if repo.last_analyzed else None,
    }


@router.get("/{owner}/{repo_name}/progress")
async def get_analysis_progress(
    owner: str,
    repo_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Poll analysis progress."""
    full_name = f"{owner}/{repo_name}"
    result = await db.execute(select(Repository).where(Repository.full_name == full_name))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "status": repo.analysis_status,
        "progress": repo.analysis_progress,
        "stage": repo.analysis_stage,
    }


@router.get("/{owner}/{repo_name}/architecture")
async def get_architecture(
    owner: str,
    repo_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get architecture diagram data (React Flow nodes/edges)."""
    result = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return repo.architecture_diagram or {"nodes": [], "edges": []}


@router.get("/{owner}/{repo_name}/file-explain")
async def explain_file(
    owner: str,
    repo_name: str,
    path: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Explain a specific file from the repository."""
    result = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    github = GitHubService(current_user.github_access_token)
    content = await github.get_file_content(owner, repo_name, path)
    if not content:
        raise HTTPException(status_code=404, detail="File not found")

    from services.agent_service import get_agent_service
    agent = get_agent_service()
    explanation = await agent.explain_file(
        str(repo.id), path, content, current_user.expertise_level or "intermediate"
    )
    return {"file_path": path, "explanation": explanation}


@router.post("/{owner}/{repo_name}/learning-path")
async def generate_learning_path(
    owner: str,
    repo_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate personalized learning path for this repository."""
    from models.learning import LearningPath
    from services.agent_service import get_agent_service

    result = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    dev_profile = {
        "expertise_level": current_user.expertise_level,
        "top_languages": current_user.top_languages or [],
        "skill_vector": current_user.skill_vector or {},
    }

    agent = get_agent_service()
    plan = await agent.generate_learning_path(str(repo.id), {
        "full_name": repo.full_name,
        "tech_stack": repo.tech_stack or [],
        "architecture_summary": repo.architecture_summary or "",
        "learning_prerequisites": repo.learning_prerequisites or [],
    }, dev_profile)

    # Save to DB
    lp = LearningPath(
        user_id=current_user.id,
        repository_id=repo.id,
        title=plan.get("title", f"Learning {repo.name}"),
        description=plan.get("description"),
        total_days=plan.get("total_days", 7),
        plan=plan.get("plan"),
    )
    db.add(lp)
    await db.commit()
    await db.refresh(lp)

    return {"learning_path_id": str(lp.id), "plan": plan}
