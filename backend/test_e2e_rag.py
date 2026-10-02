"""端到端测试：注册 → 登录 → 建会话 → 知识库问答流式接口（useKnowledge=true）

运行方式（在 backend 目录下）：
    先启动后端：venv/Scripts/python -m uvicorn app.main:app --port 8000
    再执行本脚本：venv/Scripts/python test_e2e_rag.py
"""
import asyncio
import json
import uuid

import httpx
import pymysql

BASE = "http://127.0.0.1:8000/api"
USER = f"ragtest_{uuid.uuid4().hex[:6]}"


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=60.0) as client:
        # 1. 注册 + 登录
        await client.post("/user/add", json={
            "username": USER,
            "email": f"{USER}@test.com",
            "nickname": "RAG测试",
            "password": "test123456",
        })
        login = await client.post("/user/login", json={"username": USER, "password": "test123456"})
        assert login.json()["code"] == "200", login.text
        token = login.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ 登录成功（用户 {USER}）")

        # 2. 创建会话
        sess = await client.post(
            "/psychological-chat/session/start", headers=headers,
            json={"initialMessage": "失眠怎么办", "sessionTitle": "RAG测试会话"},
        )
        session_id = sess.json()["data"]["sessionId"]
        print(f"✅ 会话已创建 sessionId={session_id}")

        # 3. 知识库问答（流式）
        full_content = ""
        async with client.stream(
            "POST", "/psychological-chat/stream", headers={**headers, "Accept": "text/event-stream"},
            json={"sessionId": session_id, "userMessageText": "失眠怎么办", "useKnowledge": True},
        ) as resp:
            assert resp.status_code == 200, f"HTTP {resp.status_code}"
            print(f"✅ 流式接口返回 {resp.status_code}")
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    payload = json.loads(line[6:])
                    content = payload.get("data", {}).get("content")
                    if content:
                        full_content += content
                except (json.JSONDecodeError, AttributeError):
                    continue

        print("\n======== 小暖的回答（截断前 600 字） ========\n")
        print(full_content[:600])

        # 4. 校验数据库：AI 消息是否带参考资料落库
        conn = pymysql.connect(
            host="localhost", port=3306, user="root", password="123456",
            database="psychology_db", charset="utf8mb4",
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT content FROM chat_messages WHERE session_id=%s AND sender_type=2 ORDER BY id DESC LIMIT 1",
            (int(session_id),),
        )
        row = cur.fetchone()
        conn.close()
        if row and "参考资料" in row[0]:
            print("✅ AI 消息已落库，包含【参考资料】列表，刷新聊天记录后引用依然可见")
        else:
            print("❌ 落库内容里没找到参考资料，请检查")


if __name__ == "__main__":
    asyncio.run(main())
