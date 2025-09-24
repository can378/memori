"""
db_connection.py
PostgreSQL 연결 및 커넥션 풀 관리 모듈
"""

import os
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from dotenv import load_dotenv

load_dotenv()
# -------------------------
# 환경변수에서 DB URL 불러오기
# -------------------------
POSTGRE_DB_URL = os.getenv("POSTGRE_DB_URL")
if not POSTGRE_DB_URL:
    raise ValueError("환경변수 POSTGRE_DB_URL이 설정되지 않았습니다.")

# SQLAlchemy Engine 생성
# 커넥션 풀 옵션 적용
# -------------------------
engine = create_engine(
    POSTGRE_DB_URL,
    pool_size=10,          # 기본 커넥션 풀 크기
    max_overflow=20,       # 풀 초과 시 생성 가능한 커넥션 수
    pool_timeout=30,       # 커넥션 풀에서 가져올 때 최대 대기 시간 (초)
    pool_recycle=1800,     # 커넥션 재사용 주기 (초) → 30분
    echo=False             # SQL 로그 출력 여부 (디버깅 시 True)
)

# -------------------------
# 세션 팩토리 및 Scoped Session
# -------------------------
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# -------------------------
# Declarative Base
# -------------------------
Base = declarative_base()

# -------------------------
# 의존성 주입 함수
# -------------------------
def get_db():
    """
    요청마다 DB 세션을 생성/해제하는 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# 테스트용 DB 연결 함수
# -------------------------
def test_connection():
    """
    DB 연결 테스트용 함수 (SELECT 1 실행)
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return False

# if __name__ == "__main__":
#     # 모듈 단독 실행 시 연결 테스트
#     if test_connection():
#         print("✅ PostgreSQL 연결 성공")
#     else:
#         print("❌ PostgreSQL 연결 실패")