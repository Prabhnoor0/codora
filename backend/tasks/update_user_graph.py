"""Developer profile analysis Celery task."""
import asyncio
from celery_app import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="tasks.update_user_graph.analyze_developer_profile", queue="default")
def analyze_developer_profile(user_id: str, github_login: str, github_token: str = None):
    asyncio.run(_analyze(user_id, github_login, github_token))


async def _analyze(user_id: str, github_login: str, github_token: str = None):
    from database import AsyncSessionLocal
    from models.user import User
    from sqlalchemy import select
    from services.github_service import GitHubService
    from services.graph_service import get_graph_service

    github = GitHubService(github_token)
    graph = get_graph_service()

    try:
        profile = await github.build_developer_profile(github_login)
        top_langs = profile.get("top_languages", [])
        lang_breakdown = profile.get("language_breakdown", {})

        # Compute expertise level
        commits = profile.get("recent_commits", 0)
        prs = profile.get("recent_prs", 0)
        repos = profile.get("total_repos", 0)

        if repos > 30 or commits > 50 or prs > 20:
            expertise = "advanced"
        elif repos > 10 or commits > 15:
            expertise = "intermediate"
        else:
            expertise = "beginner"

        # Skill vector
        skill_vector = {lang: score / 100 for lang, score in lang_breakdown.items()}

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.top_languages = top_langs
                user.language_breakdown = lang_breakdown
                user.expertise_level = expertise
                user.skill_vector = skill_vector
                user.total_commits = commits
                user.total_prs = prs
                user.profile_analyzed = True
                await db.commit()

        # Update Neo4j developer graph
        github_id_result = await github.get_user(github_login)
        github_id = github_id_result.get("id", 0)

        await graph.upsert_developer(github_id, github_login, {"avatar_url": ""})
        for lang, pct in lang_breakdown.items():
            await graph.add_technology(github_id, lang, pct)
            await graph.add_skill(github_id, lang, pct / 100)

        log.info("Developer profile analyzed", user=github_login, expertise=expertise)

    except Exception as e:
        log.error("Profile analysis failed", user=github_login, error=str(e))
