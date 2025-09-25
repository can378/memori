from memori import Memori
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

MYSQL_DSN = os.getenv("POSTGRE_DB_URL")

# 가장 간단하게 데이터베이스 연결 테스트하는 코드입니다.
# DB에 테이블이 없으면 자동 생성됩니다.
# DB에 테이블이 있으면 기존 테이블을 사용합니다.
# DB의 데이터를 잘 가져오는지랑 DB에 데이터를 잘 저장하는지도 확인하세요

client = OpenAI()
memori = Memori(
    database_connect=MYSQL_DSN,
    conscious_ingest=True,   # 단기 기억 1회 주입
    auto_ingest=True         # 질의 시 동적 검색
)
memori.enable()

def run_conversation(client, messages, label):
    print(f"======== {label} Conversation ========")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    print(response.dict())
    print(response.choices[0].message.content)


run_conversation(client, [{"role": "user", "content": "I'm yunjin, a backend developer"}], "First")
run_conversation(client, [{"role": "user", "content": "do you remember my name?"}], "Second")
run_conversation(client, [{"role": "user", "content": "what is my job?"}], "Third")
run_conversation(client, [{"role": "user", "content": "what a beautiful day!"}], "Fourth")
