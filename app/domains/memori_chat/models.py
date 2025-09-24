from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, JSON,text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from typing import Union, List, Literal,Optional, Any,Dict
from pydantic import BaseModel,Field
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
import json

Base = declarative_base()



# db table = chat_history
class ChatHistory(Base):
    __tablename__ = "chat_history"
    __table_args__ = {"schema": "public"}

    chat_id = Column(String(255), primary_key=True)
    user_input = Column(Text, nullable=False)
    ai_output = Column(Text, nullable=False)
    model = Column(String(255), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    session_id = Column(String(255), nullable=False)
    namespace = Column(String(255), nullable=False)
    tokens_used = Column(Integer)
    metadata_json = Column(JSON)
    is_final_answer = Column(String(1), nullable=True)


class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = {"schema": "public"}

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=True)
    chat_title = Column(String(255), nullable=True)
    mcp_server_session_map_id = Column(String(255), nullable=True)
    agent_model_id = Column(String(255), nullable=True)
    agent_system_prompt = Column(Text, nullable=True)
    status = Column(String(255), nullable=True)
    conversation_manager_state = Column(Integer, nullable=True)
    metadata_json = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))

    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )
    deleted_at = Column(TIMESTAMP(timezone=False), nullable=True)

# base model
class ChatHistorySchema(BaseModel):
    class Config:
        from_attributes = True

    chat_id: str
    user_input: str
    ai_output: str
    model: str
    timestamp: datetime
    session_id: str
    namespace: str
    tokens_used: Optional[int] = 0
    metadata_json: Dict[str, Any] = Field(default_factory=dict) 
    is_final_answer: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ConverseRequest(BaseModel):
    messages: Union[str, List[ChatMessage]]




def _ensure_str_metadata(md: Optional[Dict[str, Any] | str]) -> str:
    if md is None:
        return ""
    if isinstance(md, str):
        return md
    try:
        return json.dumps(md, ensure_ascii=False)
    except Exception:
        return ""

def _parse_metadata_to_dict(md: Optional[str]) -> Dict[str, Any]:
    if not md:
        return {}
    try:
        return json.loads(md)
    except Exception:
        return {"raw": md}  # 파싱 실패 시 원문 보존


class ChatSessionCreate(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    chat_title: Optional[str] = None
    mcp_server_session_map_id: Optional[str] = None
    agent_model_id: Optional[str] = None
    agent_system_prompt: Optional[str] = None
    status: Optional[str] = None
    conversation_manager_state: Optional[int] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ChatSessionUpdate(BaseModel):
    user_id: Optional[str] = None
    chat_title: Optional[str] = None
    mcp_server_session_map_id: Optional[str] = None
    agent_model_id: Optional[str] = None
    agent_system_prompt: Optional[str] = None
    status: Optional[str] = None
    conversation_manager_state: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    # soft-delete/restore는 별도 엔드포인트에서 처리


class ChatSessionRead(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    chat_title: Optional[str] = None
    mcp_server_session_map_id: Optional[str] = None
    agent_model_id: Optional[str] = None
    agent_system_prompt: Optional[str] = None
    status: Optional[str] = None
    conversation_manager_state: Optional[int] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 변환 유틸리티
def encode_metadata_for_db(md: Optional[Dict[str, Any]]) -> str:
    return _ensure_str_metadata(md)

def decode_metadata_from_db(md_text: Optional[str]) -> Dict[str, Any]:
    return _parse_metadata_to_dict(md_text)