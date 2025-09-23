from memori import Memori
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

MYSQL_DSN = os.getenv("MYSQL_DB_URL")
print(MYSQL_DSN)

client = OpenAI()
memori = Memori(
    database_connect=MYSQL_DSN,
    conscious_ingest=True,   # 단기 기억 1회 주입
    auto_ingest=True         # 질의 시 동적 검색
)
memori.enable()

print("=== First Conversation ===")
r1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "I'm yunjin, a backend developer"}]
)
print(r1.choices[0].message.content)

print("=== Second Conversation ===")
r2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "do you remember who I am?"}]
)
print(r2.choices[0].message.content)
