"""Mentor chat router — streaming AI mentor with repo context."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from database import get_db
from models.repository import Repository
from models.learning import MentorConversation
from routers.deps import get_current_user
from services.agent_service import get_agent_service

router = APIRouter()


@router.post("/chat")
async def mentor_chat(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Streaming mentor chat with repository context."""
    question = payload.get("question", "")
    repo_full_name = payload.get("repo_full_name", "")
    conversation_id = payload.get("conversation_id")
    history = payload.get("history", [])

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Load or create conversation
    repo_id = None
    if repo_full_name:
        result = await db.execute(
            select(Repository).where(Repository.full_name == repo_full_name)
        )
        repo = result.scalar_one_or_none()
        if repo:
            repo_id = str(repo.id)

    agent = get_agent_service()

    dev_profile = {
        "expertise_level": current_user.expertise_level,
        "top_languages": current_user.top_languages or [],
    }

    async def generate():
        full_response = ""
        async for chunk in agent.mentor_chat(
            repo_id or "",
            repo_full_name,
            question,
            history,
            dev_profile,
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Send done signal
        yield f"data: {json.dumps({'done': True, 'full_response': full_response})}\n\n"

        # Save to conversation history
        if conversation_id:
            try:
                result = await db.execute(
                    select(MentorConversation).where(MentorConversation.id == conversation_id)
                )
                conv = result.scalar_one_or_none()
                if conv:
                    messages = conv.messages or []
                    messages.append({"role": "user", "content": question})
                    messages.append({"role": "assistant", "content": full_response})
                    conv.messages = messages
                    await db.commit()
            except Exception:
                pass

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/conversation")
async def create_conversation(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new mentor conversation session."""
    repo_full_name = payload.get("repo_full_name")
    repo_id = None

    if repo_full_name:
        result = await db.execute(
            select(Repository).where(Repository.full_name == repo_full_name)
        )
        repo = result.scalar_one_or_none()
        if repo:
            repo_id = repo.id

    conv = MentorConversation(
        user_id=current_user.id,
        repository_id=repo_id,
        messages=[],
        title=payload.get("title", "New Conversation"),
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return {"conversation_id": str(conv.id)}


@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List user's mentor conversations."""
    result = await db.execute(
        select(MentorConversation)
        .where(MentorConversation.user_id == current_user.id)
        .order_by(MentorConversation.updated_at.desc())
        .limit(20)
    )
    convs = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "message_count": len(c.messages or []),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in convs
    ]
