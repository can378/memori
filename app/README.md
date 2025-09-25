
# SETTING
.env
```
OPENAI_API_KEY=
VLLM_BASE_URL=

POSTGRE_DB_URL=postgresql+psycopg2://:@localhost:/
```
# DB connection test
memory/databse/manager/db_connection.py에서 주석빼고 단일 실행

# RUN
루트에서 실행
uvicorn app.main:app --reload
