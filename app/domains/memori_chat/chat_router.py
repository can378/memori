from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.db_connection import get_db

router = APIRouter(prefix="/chat", tags=["chat"])

from app.core.context import use_session, ause_session, bind_stream, get_session_id, set_session_id, reset_session_id   
from app.domains.memori_chat import services
from app.domains.memori_chat.models import (
    ConverseRequest, 
    ChatHistorySchema,
    ChatPair,
    ConverseIn
)




######################################
# chat history
######################################
@router.get("/history", response_model=List[ChatHistorySchema])
def get_chat_history(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    return services.get_recent_chat_history(db, limit=limit)


@router.get("/history/current-session", response_model=List[ChatPair])
def get_current_session_chat_history(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    sid = get_session_id()
    if not sid:
        raise HTTPException(status_code=400, detail="No session_id in context")
    return services.get_chats_by_session(db, session_id=sid, limit=limit)


@router.get("/sessions/{session_id}/chats", response_model=List[ChatPair])
def get_session_chats(session_id: str, limit: int = 50, db: Session = Depends(get_db)):
    return services.get_chats_by_session(db, session_id=session_id, limit=limit)


@router.post("/converse", response_model=ChatHistorySchema)
def converse_and_save(payload: ConverseIn, db: Session = Depends(get_db)):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages is empty")

    # 1) 세션 확보(없으면 생성)
    sid=get_session_id()
    if not sid:
        raise HTTPException(status_code=400, detail="No session_id in context")
    
    # 2) 요청 스코프에 session_id 주입
    token = set_session_id(sid)
    try:
        # 3) 실행+저장 (서비스가 session_id로 chat_history에 저장)
        normalized = payload.messages  # 이미 [{role, content}]
        record = services.run_and_save_conversation(
            db=db,
            messages=normalized,
            session_id=sid,
            user_id=payload.user_id,
        )
        return record
    finally:
        reset_session_id(token)
