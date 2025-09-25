from fastapi import FastAPI, Request
from app.core.db_connection import test_connection
from app.domains.memori_chat.chat_router import router as memori_chat_router
from app.domains.memori_chat.session_router import router as memori_chat_session_router
from app.core.context import set_session_id, reset_session_id 

app = FastAPI()

# default api====================================================
@app.get("/")
def root():
    return {"message": "Hello!"}

@app.get("/db/health")
def health_check():
    """DB 연결 여부 확인"""
    ok = test_connection()
    return {"db_connection": "ok" if ok else "failed"}


# 전달받은 cookie의 session_id를 ContextVar에 세팅===================
@app.middleware("http")
async def session_cookie_ctx(request: Request, call_next):
    sid = request.cookies.get("session_id")
    token = set_session_id(sid)
    try:
        response = await call_next(request)
        return response
    finally:
        reset_session_id(token)


# add routers======================================================
app.include_router(memori_chat_router)
app.include_router(memori_chat_session_router)