from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from db.database import get_db
from db.models import User, Message
from api.auth import get_current_user
from agents.orchestrator import run_orchestrator
import uuid

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.user_id == current_user.id)
        .order_by(Message.created_at)
        .limit(20)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in result.scalars().all()
    ]

    user_msg = Message(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.commit()

    response = await run_orchestrator(
        message=request.message,
        history=history,
        user_id=current_user.id,
        user_role=current_user.role.value,
    )

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        role="assistant",
        content=response,
    )
    db.add(assistant_msg)
    await db.commit()

    return {"response": response}


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.user_id == current_user.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]
