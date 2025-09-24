# app/models.py
from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from typing import Union, List, Literal
from pydantic import BaseModel
Base = declarative_base()

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


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ConverseRequest(BaseModel):
    messages: Union[str, List[ChatMessage]]