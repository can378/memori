from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.db_connection import get_db

router = APIRouter(prefix="/chat", tags=["chat"])

from app.domains.memori_chat import services
from app.domains.memori_chat.models import (
    ConverseRequest, 
    ChatHistorySchema,
)


from pydantic import BaseModel, Field
class ConverseIn(BaseModel):
    session_id: str | None = None
    user_id: str | None = None
    messages: list[dict]  # [{role, content}, ...]


######################################
# chat history
######################################
@router.get("/history", response_model=List[ChatHistorySchema])
def get_chat_history(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    return services.get_recent_chat_history(db, limit=limit)


@router.post("/converse", response_model=ChatHistorySchema)
def converse_and_save(payload: ConverseRequest, db: Session = Depends(get_db)):

    if isinstance(payload.messages, str):
        if not payload.messages.strip():
            raise HTTPException(status_code=400, detail="messages is empty")
        normalized = [{"role": "user", "content": payload.messages}]
    else:
        if not payload.messages:
            raise HTTPException(status_code=400, detail="messages is empty")
        normalized = [m.model_dump() for m in payload.messages]

    record = services.run_and_save_conversation(db=db, messages=normalized)
    return record
