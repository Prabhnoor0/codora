"""Issues router — recommendations, readiness scores, tutor."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from database import get_db
from models.repository import Repository
from models.issue import Issue, IssueRecommendation
from routers.deps import get_current_user
from services.agent_service import get_agent_service
from services.rag_service import get_rag_service

router = APIRouter()
log = structlog.get_logger()


@router.get("/{owner}/{repo_name}/recommended")
async def get_recommended_issues(
    owner: str,
    repo_name: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get personalized issue recommendations for the current user."""
    result = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Fetch open issues
    result = await db.execute(
        select(Issue)
        .where(and_(Issue.repository_id == repo.id, Issue.state == "open"))
        .limit(limit)
    )
    issues = result.scalars().all()

    dev_profile = {
        "expertise_level": current_user.expertise_level or "beginner",
        "top_languages": current_user.top_languages or [],
        "skill_vector": current_user.skill_vector or {},
    }
    repo_data = {
        "full_name": repo.full_name,
        "tech_stack": repo.tech_stack or [],
        "learning_prerequisites": repo.learning_prerequisites or [],
    }

    agent = get_agent_service()
    enriched_issues = []

    for issue in issues:
        issue_dict = {
            "id": str(issue.id),
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "labels": issue.labels or [],
            "difficulty": issue.difficulty or "medium",
            "required_skills": issue.required_skills or [],
            "github_url": issue.github_url,
        }

        # Check if readiness score is cached
        rec_result = await db.execute(
            select(IssueRecommendation).where(
                and_(
                    IssueRecommendation.user_id == current_user.id,
                    IssueRecommendation.issue_id == issue.id,
                )
            )
        )
        cached_rec = rec_result.scalar_one_or_none()

        if cached_rec:
            issue_dict["readiness_score"] = cached_rec.readiness_score
            issue_dict["missing_skills"] = cached_rec.missing_skills
        else:
            # Calculate readiness score
            try:
                readiness = await agent.calculate_readiness(issue_dict, dev_profile, repo_data)
                issue_dict["readiness_score"] = readiness.get("readiness_score", 50)
                issue_dict["missing_skills"] = readiness.get("missing_skills", [])
                issue_dict["recommendation"] = readiness.get("recommendation", "")

                # Cache it
                rec = IssueRecommendation(
                    user_id=current_user.id,
                    issue_id=issue.id,
                    repository_id=repo.id,
                    readiness_score=readiness.get("readiness_score", 50),
                    missing_skills=readiness.get("missing_skills", []),
                )
                db.add(rec)
                await db.commit()
            except Exception as e:
                log.warning("Readiness calculation failed", error=str(e))
                issue_dict["readiness_score"] = 50
                issue_dict["missing_skills"] = []

        enriched_issues.append(issue_dict)

    # Sort by readiness score descending
    enriched_issues.sort(key=lambda x: x.get("readiness_score", 0), reverse=True)
    return enriched_issues


@router.get("/{owner}/{repo_name}/{issue_number}/tutor")
async def get_issue_tutor(
    owner: str,
    repo_name: str,
    issue_number: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get issue tutor content — converts issue into learning experience."""
    result = await db.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo_name}")
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(Issue).where(
            and_(Issue.repository_id == repo.id, Issue.number == issue_number)
        )
    )
    issue = result.scalar_one_or_none()
    if not issue:
        # Try fetching from GitHub
        from services.github_service import GitHubService
        github = GitHubService(current_user.github_access_token)
        raw_issue = await github.get_issue(owner, repo_name, issue_number)
        issue_dict = {
            "number": raw_issue["number"],
            "title": raw_issue["title"],
            "body": raw_issue.get("body", ""),
            "labels": [l["name"] for l in raw_issue.get("labels", [])],
        }
    else:
        issue_dict = {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "labels": issue.labels or [],
        }

    dev_profile = {
        "expertise_level": current_user.expertise_level or "beginner",
        "top_languages": current_user.top_languages or [],
    }

    agent = get_agent_service()
    tutor_content = await agent.tutor_issue(
        str(repo.id), repo.full_name, issue_dict, dev_profile
    )

    # Predict affected files
    rag = get_rag_service()
    affected_files = await rag.find_similar_files(
        str(repo.id),
        f"{issue_dict['title']} {issue_dict['body'][:300]}",
        top_k=8
    )

    return {
        "issue": issue_dict,
        "tutor": tutor_content,
        "affected_files": affected_files,
    }
