# app/domains/memori_chat/router.py
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db_connection import get_db
from app.domains.memori_chat import services
from app.domains.memori_chat.models import (
    ChatSession,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionRead,
)

router = APIRouter(prefix="/chat-sessions", tags=["chat-sessions"])

@router.post("", response_model=ChatSessionRead)
def api_create_chat_session(payload: ChatSessionCreate, db: Session = Depends(get_db)):
    if services.get_chat_session(db, payload.session_id, include_deleted=True):
        raise HTTPException(status_code=409, detail="session_id already exists")
    entity: ChatSession = services.create_chat_session(db, payload)
    return ChatSessionRead.from_orm(entity)

@router.get("/{session_id}", response_model=ChatSessionRead)
def api_get_chat_session(session_id: str, include_deleted: bool = False, db: Session = Depends(get_db)):
    entity = services.get_chat_session(db, session_id, include_deleted=include_deleted)
    if not entity:
        raise HTTPException(status_code=404, detail="session not found")
    return ChatSessionRead.from_orm(entity)

@router.get("", response_model=List[ChatSessionRead])
def api_list_chat_sessions(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    include_deleted: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, _total = services.list_chat_sessions(
        db, user_id=user_id, status=status, include_deleted=include_deleted, offset=offset, limit=limit
    )
    return [ChatSessionRead.from_orm(r) for r in rows]

@router.patch("/{session_id}", response_model=ChatSessionRead)
def api_update_chat_session(session_id: str, payload: ChatSessionUpdate, db: Session = Depends(get_db)):
    entity = services.update_chat_session(db, session_id, payload)
    if not entity:
        raise HTTPException(status_code=404, detail="session not found or deleted")
    return ChatSessionRead.from_orm(entity)

@router.delete("/{session_id}")
def api_soft_delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    ok = services.soft_delete_chat_session(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found or already deleted")
    return {"ok": True}

@router.post("/{session_id}/restore")
def api_restore_chat_session(session_id: str, db: Session = Depends(get_db)):
    ok = services.restore_chat_session(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found or not deleted")
    return {"ok": True}

@router.delete("/{session_id}/hard")
def api_hard_delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    ok = services.hard_delete_chat_session(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found")
    return {"ok": True}
