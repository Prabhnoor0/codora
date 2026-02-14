"""Auth router — GitHub OAuth flow and JWT issuance."""
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from config import settings
from database import get_db
from models.user import User
from services.github_service import GitHubService

router = APIRouter()
log = structlog.get_logger()

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


def create_jwt(user_id: str, github_login: str) -> str:
    payload = {
        "sub": str(user_id),
        "github_login": github_login,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth with explicit callback to backend."""
    callback = settings.GITHUB_CALLBACK_URL
    params = (
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=read:user,user:email,repo"
        f"&redirect_uri={callback}"
    )
    return RedirectResponse(f"{GITHUB_AUTH_URL}{params}")


@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback, create/update user, return JWT."""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_CALLBACK_URL,
            },
        )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

    # Fetch GitHub user
    github = GitHubService(access_token)
    github_user = await github.get_current_user()
    github_id = github_user["id"]

    # Upsert user in DB
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            github_id=github_id,
            github_login=github_user["login"],
            github_name=github_user.get("name"),
            github_email=github_user.get("email"),
            github_avatar_url=github_user.get("avatar_url"),
            github_bio=github_user.get("bio"),
            github_location=github_user.get("location"),
            github_company=github_user.get("company"),
            github_blog=github_user.get("blog"),
            github_followers=github_user.get("followers", 0),
            github_following=github_user.get("following", 0),
            github_public_repos=github_user.get("public_repos", 0),
            github_access_token=access_token,
        )
        db.add(user)
        await db.flush()

        # Trigger async profile analysis
        from tasks.update_user_graph import analyze_developer_profile
        analyze_developer_profile.delay(str(user.id), github_user["login"], access_token)
    else:
        user.github_access_token = access_token
        user.last_github_sync = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    token = create_jwt(str(user.id), user.github_login)

    # Redirect to frontend with token
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={token}")


@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh JWT token."""
    # Implementation: verify old token, issue new one
    pass


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current authenticated user."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth[7:]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "github_login": user.github_login,
        "github_name": user.github_name,
        "github_avatar_url": user.github_avatar_url,
        "top_languages": user.top_languages,
        "expertise_level": user.expertise_level,
        "skill_vector": user.skill_vector,
        "profile_analyzed": user.profile_analyzed,
    }
