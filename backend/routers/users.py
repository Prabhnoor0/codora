"""Users and knowledge graph router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database import get_db
from models.user import User
from models.learning import LearningPath, LearningProgress
from routers.deps import get_current_user
from services.graph_service import get_graph_service
from services.github_service import GitHubService

router = APIRouter()


@router.post("/me/skills")
async def save_skills(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Save user skills AND always merge with real GitHub commit-frequency weighted data."""
    listed_skills = payload.get("skills", [])
    experience = payload.get("experience_level", "beginner")
    interests = payload.get("interests", [])

    # Always scan GitHub to get real language usage (commit frequency proxy)
    github = GitHubService(current_user.github_access_token)
    try:
        profile = await github.build_developer_profile(current_user.github_login)
        github_langs = profile.get("language_breakdown", {})  # {Python: 45.2, JS: 30.1}
        github_top = profile.get("top_languages", [])
        current_user.language_breakdown = github_langs
        current_user.total_commits = profile.get("recent_commits", 0)
        current_user.total_prs = profile.get("recent_prs", 0)
        current_user.last_github_sync = datetime.utcnow()

        # Build weighted skill_vector: normalise github bytes (0-1) + boost listed skills
        max_pct = max(github_langs.values()) if github_langs else 1.0
        skill_vector: dict = {}
        for lang, pct in github_langs.items():
            skill_vector[lang] = round(pct / max_pct, 3)
        for skill in listed_skills:
            skill_vector[skill] = min(1.0, skill_vector.get(skill, 0.5) + 0.2)
        current_user.skill_vector = skill_vector

        # Merge top languages: github-detected first, then any extra listed ones
        merged = list(github_top)
        for s in listed_skills:
            if s not in merged:
                merged.append(s)
        current_user.top_languages = merged[:10]
    except Exception:
        current_user.top_languages = listed_skills
        current_user.skill_vector = {s: 0.7 for s in listed_skills}

    current_user.expertise_level = experience
    current_user.contribution_domains = interests
    current_user.profile_analyzed = True
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    return {
        "success": True,
        "skills": current_user.top_languages,
        "skill_vector": current_user.skill_vector,
        "experience_level": experience,
    }


@router.get("/me/github-scan")
async def scan_github_profile(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Scan GitHub and build commit-frequency weighted skill_vector."""
    github = GitHubService(current_user.github_access_token)
    try:
        profile = await github.build_developer_profile(current_user.github_login)
        github_langs = profile.get("language_breakdown", {})
        current_user.top_languages = profile.get("top_languages", [])
        current_user.language_breakdown = github_langs
        current_user.total_commits = profile.get("recent_commits", 0)
        current_user.total_prs = profile.get("recent_prs", 0)
        current_user.last_github_sync = datetime.utcnow()

        max_pct = max(github_langs.values()) if github_langs else 1.0
        skill_vector = {lang: round(pct / max_pct, 3) for lang, pct in github_langs.items()}
        current_user.skill_vector = skill_vector

        total_repos = profile.get("total_repos", 0)
        if total_repos > 30 or profile.get("recent_prs", 0) > 20:
            current_user.expertise_level = "advanced"
        elif total_repos > 10 or profile.get("recent_commits", 0) > 50:
            current_user.expertise_level = "intermediate"
        else:
            current_user.expertise_level = "beginner"

        await db.commit()
        return {
            "success": True,
            "top_languages": current_user.top_languages,
            "skill_vector": skill_vector,
            "expertise_level": current_user.expertise_level,
            "total_repos": total_repos,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/me/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed developer profile."""
    graph = get_graph_service()
    graph_data = await graph.get_developer_knowledge_graph(current_user.github_id)

    result = await db.execute(
        select(LearningPath)
        .where(LearningPath.user_id == current_user.id)
        .order_by(LearningPath.updated_at.desc())
        .limit(5)
    )
    learning_paths = result.scalars().all()

    return {
        "user": {
            "id": str(current_user.id),
            "github_login": current_user.github_login,
            "github_name": current_user.github_name,
            "github_avatar_url": current_user.github_avatar_url,
            "expertise_level": current_user.expertise_level,
            "top_languages": current_user.top_languages,
            "language_breakdown": current_user.language_breakdown,
            "total_commits": current_user.total_commits,
            "total_prs": current_user.total_prs,
        },
        "knowledge_graph": graph_data,
        "learning_paths": [
            {
                "id": str(lp.id),
                "title": lp.title,
                "completion_percentage": lp.completion_percentage,
                "xp_points": lp.xp_points,
                "streak_days": lp.streak_days,
            }
            for lp in learning_paths
        ],
    }


@router.get("/me/knowledge-graph")
async def get_knowledge_graph(current_user=Depends(get_current_user)):
    """Get developer knowledge graph for visualization."""
    graph = get_graph_service()
    return await graph.get_developer_knowledge_graph(current_user.github_id)


@router.post("/me/learning/{path_id}/progress")
async def update_learning_progress(
    path_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a learning day as complete."""
    result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    lp = result.scalar_one_or_none()
    if not lp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Learning path not found")

    day = payload.get("day", 1)
    progress = LearningProgress(
        learning_path_id=lp.id,
        user_id=current_user.id,
        day=day,
        topic=payload.get("topic", ""),
        completed=True,
        xp_earned=payload.get("xp", 100),
    )
    db.add(progress)

    # Update path stats
    lp.current_day = max(lp.current_day, day)
    lp.xp_points += payload.get("xp", 100)
    lp.completion_percentage = round((lp.current_day / lp.total_days) * 100, 1)

    # Update knowledge graph
    if lp.repository_id:
        from models.repository import Repository
        res = await db.execute(select(Repository).where(Repository.id == lp.repository_id))
        repo = res.scalar_one_or_none()
        if repo:
            graph = get_graph_service()
            await graph.track_learning_progress(
                current_user.github_id, payload.get("topic", ""), repo.full_name
            )

    await db.commit()
    return {"success": True, "xp_earned": payload.get("xp", 100), "total_xp": lp.xp_points}
