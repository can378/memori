from fastapi import APIRouter, Depends

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db_connection import get_db
from app.domains.memori_chat.services import (
    run_and_save_conversation,
)

router = APIRouter(prefix="/chat", tags=["chat"])
from app.domains.memori_chat.models import ConverseRequest


@router.get("/history")
def get_chat_history(db: Session = Depends(get_db)):
    # 필요하면 ORDER BY timestamp DESC 등 추가
    result = db.execute(text("SELECT * FROM public.chat_history ORDER BY timestamp DESC LIMIT 10"))
    return [dict(row._mapping) for row in result]


@router.post("/converse")
def converse_and_save(payload: ConverseRequest, db: Session = Depends(get_db)):
    if isinstance(payload.messages, str):
        normalized = [{"role": "user", "content": payload.messages}]
    else:
        normalized = [m.model_dump() for m in payload.messages]

    record = run_and_save_conversation(
        db=db,
        messages=normalized,
    )
