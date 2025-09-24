# app/domains/memori_chat/services.py
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any,Optional, Tuple
from sqlalchemy import select, func

from sqlalchemy import text
from sqlalchemy.orm import Session
from openai import OpenAI
from memori import Memori
from dotenv import load_dotenv
import os


from app.domains.memori_chat.models import ChatSession
from app.domains.memori_chat.models import (
    ChatHistory,
    ChatSession,
    ChatSessionCreate,
    ChatSessionUpdate,
)

# get vairables from .env
load_dotenv()
DB_URL = os.getenv("POSTGRE_DB_URL")


# open ai / memori
client = OpenAI()
memori = Memori(
    database_connect=DB_URL,
    conscious_ingest=True,
    auto_ingest=True
)
memori.enable()



#####################################
# get recent chat history
#####################################
def get_recent_chat_history(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        text("""
            SELECT *
            FROM public.chat_history
            ORDER BY timestamp DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    return [dict(r._mapping) for r in rows]


#####################################
# get chat conversation and save to db
#####################################
def run_and_save_conversation(
    db: Session,
    messages: List[Dict[str, Any]],
) -> ChatHistory:
    """
    OpenAI 대화 1건 실행 후 chat_history에 저장
    """
    AI_MODEL = "gpt-4o-mini"
    # Ask OpenAI===============================
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=messages
    )

    # Organize values==========================
    chat_id = str(uuid.uuid4())
    user_input = messages[0]["content"] if messages else ""
    ai_output = response.choices[0].message.content
    model = AI_MODEL

    kst_now = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_now.replace(tzinfo=None)

    usage = getattr(response, "usage", None)
    tokens_used = getattr(usage, "total_tokens", 0) if usage else 0
    metadata_json = response.usage.dict() if usage else {}

    record = ChatHistory(
        chat_id=chat_id,
        user_input=user_input,
        ai_output=ai_output,
        model=model,
        timestamp=timestamp,
        session_id="test_session0",
        namespace="test_namespace",
        tokens_used=tokens_used,
        metadata_json=metadata_json,
        is_final_answer="1",
    )

    # Save to DB===============================
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise
    return record

#####################################
# handle session(chat room)
######################################

def create_chat_session(db: Session, payload: ChatSessionCreate) -> ChatSession:
    entity = ChatSession(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity

def get_chat_session(db: Session, session_id: str, include_deleted: bool = False) -> Optional[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.session_id == session_id)
    if not include_deleted:
        stmt = stmt.where(ChatSession.deleted_at.is_(None))
    return db.execute(stmt).scalar_one_or_none()

def list_chat_sessions(
    db: Session,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    include_deleted: bool = False,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[ChatSession], int]:
    stmt = select(ChatSession)
    if user_id:
        stmt = stmt.where(ChatSession.user_id == user_id)
    if status:
        stmt = stmt.where(ChatSession.status == status)
    if not include_deleted:
        stmt = stmt.where(ChatSession.deleted_at.is_(None))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(ChatSession.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()
    return rows, total

def update_chat_session(db: Session, session_id: str, payload: ChatSessionUpdate) -> Optional[ChatSession]:
    entity = get_chat_session(db, session_id)
    if not entity:
        return None
    # session_id는 변경 금지
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entity, k, v)
    # SQLA 2.0은 변경 추적됨 → commit만 하면 updated_at onupdate=func.now()가 반영됨
    db.commit()
    db.refresh(entity)
    return entity

def soft_delete_chat_session(db: Session, session_id: str) -> bool:
    entity = get_chat_session(db, session_id)
    if not entity:
        return False
    from sqlalchemy.sql import func as _func
    entity.deleted_at = _func.now()
    entity.updated_at = _func.now()
    db.commit()
    return True

def restore_chat_session(db: Session, session_id: str) -> bool:
    # 삭제된 것도 포함해서 가져온 뒤 복원
    entity = get_chat_session(db, session_id, include_deleted=True)
    if not entity or entity.deleted_at is None:
        return False
    from sqlalchemy.sql import func as _func
    entity.deleted_at = None
    entity.updated_at = _func.now()
    db.commit()
    return True

def hard_delete_chat_session(db: Session, session_id: str) -> bool:
    entity = get_chat_session(db, session_id, include_deleted=True)
    if not entity:
        return False
    db.delete(entity)
    db.commit()
    return True


def get_or_create_session(
    db: Session,
    desired_session_id: str | None,
    *,
    user_id: str | None = None,
    chat_title: str | None = None,
    metadata_json: dict | None = None,
) -> ChatSession:
    
    if desired_session_id:
        found = db.execute(
            select(ChatSession).where(
                ChatSession.session_id == desired_session_id,
                ChatSession.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if found:
            return found

    new_id = desired_session_id or f"sess_{uuid.uuid4().hex[:12]}"
    ent = ChatSession(
        session_id=new_id,
        user_id=user_id,
        chat_title=chat_title or "New Session",
        status="active",
        metadata_json=metadata_json or {},
    )
    db.add(ent); db.commit(); db.refresh(ent)
    return ent