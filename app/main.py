from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db_connection import get_db, test_connection
from app.domains.memori_chat.chat_router import router as memori_chat_router
from app.domains.memori_chat.session_router import router as memori_chat_session_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello!"}

@app.get("/db/health")
def health_check():
    """DB 연결 여부 확인"""
    ok = test_connection()
    return {"db_connection": "ok" if ok else "failed"}

app.include_router(memori_chat_router)
app.include_router(memori_chat_session_router)