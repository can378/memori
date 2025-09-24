# app/domains/memori_chat/services.py
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from openai import OpenAI
from memori import Memori
from dotenv import load_dotenv
import os

from app.domains.memori_chat.models import Base, ChatHistory

# --- 초기화 (한 번만) ---
load_dotenv()
DB_URL = os.getenv("POSTGRE_DB_URL")

client = OpenAI()
memori = Memori(
    database_connect=DB_URL,
    conscious_ingest=True,
    auto_ingest=True
)
memori.enable()



def run_and_save_conversation(
    db: Session,
    messages: List[Dict[str, Any]],
) -> ChatHistory:
    """
    OpenAI 대화 1건 실행 후 chat_history에 저장
    """
    # OpenAI 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # 값 정리
    chat_id = str(uuid.uuid4())
    user_input = messages[0]["content"] if messages else ""
    ai_output = response.choices[0].message.content
    model = response.model

    # postgres: timestamp without time zone → naive 추천
    # KST naive 저장
    kst_now = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_now.replace(tzinfo=None)

    tokens_used = response.usage.total_tokens
    metadata_json = response.usage.dict()  # SQLAlchemy JSON 컬럼에 dict로 넣으면 자동 직렬화

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

    db.add(record)
    db.commit()
    db.refresh(record)
    return record
