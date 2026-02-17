"""PR Review router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.pr_review import PRReview
from routers.deps import get_current_user
from services.github_service import GitHubService
from services.agent_service import get_agent_service

router = APIRouter()


@router.post("/review")
async def review_pull_request(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """AI review of a pull request."""
    repo_full_name = payload.get("repo_full_name", "")
    pr_number = payload.get("pr_number")

    if not repo_full_name or not pr_number:
        raise HTTPException(status_code=400, detail="repo_full_name and pr_number required")

    owner, repo_name = repo_full_name.split("/", 1)
    github = GitHubService(current_user.github_access_token)

    # Fetch PR data and diff
    pr_data, diff = await __import__("asyncio").gather(
        github.get_pr(owner, repo_name, pr_number),
        github.get_pr_diff(owner, repo_name, pr_number),
    )

    # Get repo_id if analyzed
    from sqlalchemy import select
    from models.repository import Repository
    result = await db.execute(select(Repository).where(Repository.full_name == repo_full_name))
    repo = result.scalar_one_or_none()
    repo_id = str(repo.id) if repo else ""

    agent = get_agent_service()
    review = await agent.review_pr(repo_id, repo_full_name, pr_data, diff)

    # Persist review
    pr_review = PRReview(
        user_id=current_user.id,
        repository_full_name=repo_full_name,
        pr_number=pr_number,
        pr_title=pr_data.get("title"),
        pr_url=pr_data.get("html_url"),
        overall_assessment=review.get("overall_assessment"),
        quality_score=review.get("quality_score"),
        bugs=review.get("bugs", []),
        security_issues=review.get("security_issues", []),
        performance_issues=review.get("performance_issues", []),
        style_issues=review.get("style_issues", []),
        architecture_violations=review.get("architecture_violations", []),
        positive_aspects=review.get("positive_aspects", []),
        suggestions=review.get("suggestions", []),
    )
    db.add(pr_review)
    await db.commit()
    await db.refresh(pr_review)

    return {"review_id": str(pr_review.id), "review": review}


@router.get("/history")
async def get_review_history(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get user's PR review history."""
    from sqlalchemy import select
    result = await db.execute(
        select(PRReview)
        .where(PRReview.user_id == current_user.id)
        .order_by(PRReview.created_at.desc())
        .limit(20)
    )
    reviews = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "repo": r.repository_full_name,
            "pr_number": r.pr_number,
            "pr_title": r.pr_title,
            "quality_score": r.quality_score,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]
