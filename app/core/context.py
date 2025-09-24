from __future__ import annotations
import contextvars
from contextlib import contextmanager, asynccontextmanager
from typing import Optional, Iterator, AsyncIterator, AsyncGenerator, Dict, Any, Callable

# 요청/태스크 로컬 세션 ID
_MEMORI_SESSION_ID: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "MEMORI_SESSION_ID", default=None
)

def get_session_id() -> Optional[str]:
    return _MEMORI_SESSION_ID.get()

def set_session_id(session_id: Optional[str]):
    """set 후 반환되는 token은 반드시 reset에 넘겨야 함."""
    return _MEMORI_SESSION_ID.set(session_id)

def reset_session_id(token) -> None:
    _MEMORI_SESSION_ID.reset(token)

@contextmanager
def use_session(session_id: Optional[str]) -> Iterator[None]:
    """동기 컨텍스트: with use_session(sid): ..."""
    tok = set_session_id(session_id)
    try:
        yield
    finally:
        reset_session_id(tok)

@asynccontextmanager
async def ause_session(session_id: Optional[str]) -> AsyncIterator[None]:
    """비동기 컨텍스트: async with ause_session(sid): ..."""
    tok = set_session_id(session_id)
    try:
        yield
    finally:
        reset_session_id(tok)

def bind_stream(session_id: str, agen: AsyncGenerator[Any, None]) -> AsyncGenerator[Any, None]:
    """
    스트리밍 제너레이터에 세션 바인딩.
    사용예:
        return bind_stream(session_id, agent.stream_async(msg))
    """
    tok = set_session_id(session_id)

    async def _wrapped():
        try:
            async for chunk in agen:
                yield chunk
        finally:
            reset_session_id(tok)

    return _wrapped()

def attach_session_to_openai_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenAI 호출 인자에 session_id 주입(인터셉터가 읽기 쉬운 위치).
    라우터/서비스에서 호출하거나, 패치 훅에서 호출.
    """
    sid = get_session_id()
    if not sid:
        return payload
    payload.setdefault("extra_body", {}).setdefault("memori", {})["session_id"] = sid
    # 필요시 백업 경로:
    payload.setdefault("extra_headers", {})["x-memori-session-id"] = sid
    return payload
