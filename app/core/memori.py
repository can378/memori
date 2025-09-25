from threading import Lock
from typing import Dict, Set, Optional
from app.core.context import get_session_id
from dotenv import load_dotenv
import os
load_dotenv()

DB_URL = os.getenv("POSTGRE_DB_URL")
_memori = None
_enabled_global = False
_enabled_sids: Set[str] = set()

_global_lock = Lock()
_sid_locks: Dict[str, Lock] = {}

def enable_memori_for_current_session_if_needed():
    
    print("🍀🍀🍀enable_memori_for_current_session_if_needed called🍀🍀🍀")
    # get current session id
    sid: Optional[str] = get_session_id()
    if not sid:
        return  # 현재 세션 없으면 아무것도 안 함

    # memori
    global _memori, _enabled_global

    # 1) Memori 싱글톤 보장 + (필요 시) 글로벌 enable 1회
    if _memori is None or not _enabled_global:
        with _global_lock:
            if _memori is None:
                from memori import Memori
                _memori = Memori(
                    database_connect=DB_URL,
                    conscious_ingest=True,
                    auto_ingest=True,
                )
            if not _enabled_global:
                # Memori.enable()이 "전역 1회 초기화"라면 여기서만 실행
                _memori.enable()
                _enabled_global = True

    # 2) 세션별 1회 가드 (경쟁 방지)
    if sid in _enabled_sids:
        return
    lock = _sid_locks.setdefault(sid, Lock())
    with lock:
        if sid in _enabled_sids:
            return
        # (필요시) 세션 의존 초기화가 있다면 여기서 수행:
        # e.g. _memori.warmup_for_session(sid)
        _enabled_sids.add(sid)
