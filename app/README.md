db 연결 실험
python example.py
python tests/connect_database/mariadb_conn_test.py

혹은
memory/databse/manager/db_connection.py에서 주석빼고 하면됨



루트에서 실행
uvicorn app.main:app --reload
