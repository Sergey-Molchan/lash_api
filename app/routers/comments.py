from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Comment
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/comments", tags=["comments"])

AVAILABLE_EMOJIS = ["😊", "😍", "🥰", "😘", "👍", "🔥", "💖", "✨", "💯", "😎", "🤩", "💪", "👏", "🙌"]

class CommentCreate(BaseModel):
    client_name: str
    client_phone: str
    rating: int = 5
    text: str
    emoji: str = "😊"

class CommentResponse(BaseModel):
    id: int
    client_name: str
    rating: int
    text: str
    emoji: str
    created_at: datetime
    is_approved: bool
    class Config:
        from_attributes = True

@router.post("/add")
async def add_comment(comment: CommentCreate, db: AsyncSession = Depends(get_db)):
    if len(comment.text) < 5:
        raise HTTPException(400, "Комментарий слишком короткий")
    if comment.emoji not in AVAILABLE_EMOJIS:
        comment.emoji = "😊"
    db_comment = Comment(
        client_name=comment.client_name[:50],
        client_phone=comment.client_phone[:20],
        rating=comment.rating,
        text=comment.text[:500],
        emoji=comment.emoji,
        is_approved=False
    )
    db.add(db_comment)
    await db.commit()
    return {"ok": True, "id": db_comment.id}

@router.get("/approved", response_model=List[CommentResponse])
async def get_approved_comments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.is_approved == True).order_by(Comment.created_at.desc()).limit(20))
    return result.scalars().all()

@router.get("/pending", response_model=List[CommentResponse])
async def get_pending_comments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.is_approved == False).order_by(Comment.created_at.desc()))
    return result.scalars().all()

@router.post("/approve/{comment_id}")
async def approve_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(404, "Комментарий не найден")
    comment.is_approved = True
    await db.commit()
    return {"ok": True}

@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(404, "Комментарий не найден")
    await db.delete(comment)
    await db.commit()
    return {"ok": True}