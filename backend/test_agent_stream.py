"""流式 Agent 冒烟测试（课 3 验收 · 后端侧）

运行（backend 目录下，需 MySQL 已启动）：
    venv/Scripts/python test_agent_stream.py

验证三件事：
  1. 正文以很多小片段到达，且"流式拼接长度 == done 完整长度"（保证没丢字）
  2. 近况/知识类问题能看到 event:tool 的 running → done
  3. 闲聊类问题没有 tool 事件，正文直接流
前端侧的验收（工具轨迹 UI）在浏览器里做，见讲义。
"""
import asyncio
import json
import logging

from app.core.database import AsyncSessionLocal
from app.services import chat_service
from app.services.agent import make_stream_agent
from test_agent import seed   # 复用课 2 的测试数据准备（测试用户 + 5 条日记）


async def run_stream(db, stream_fn, session_id, text, label):
    print(f"\n{'=' * 24}\n{label}｜用户：{text}")
    await chat_service.add_message(db, session_id, 1, text)

    pieces = []
    tool_events = []
    done_content = ""
    error = None

    async for block in stream_fn(session_id, text):
        ev, data = "message", {}
        for line in block.strip().split("\n"):
            if line.startswith("event: "):
                ev = line[7:]
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass
        if ev == "tool":
            tool_events.append((data.get("name"), data.get("status")))
            print(f"  [tool ] {data.get('label', data.get('name'))} -> {data.get('status')}")
        elif ev == "done":
            done_content = data.get("content", "")
        elif ev == "error":
            error = data
            print(f"  [error] {data}")
        else:
            content = (data.get("data") or {}).get("content")
            if content:
                pieces.append(content)

    joined = "".join(pieces)
    status = "一致 ✅" if joined == done_content else "不一致 ❌"
    print(f"  [流式 ] {len(pieces)} 个片段，拼接长度 {len(joined)}")
    print(f"  [done ] 完整长度 {len(done_content)}，与流式拼接{status}")
    print(f"  [预览 ] {done_content[:100]}...")
    if error:
        print(f"  [异常 ] {error}")
    return tool_events


async def main():
    async with AsyncSessionLocal() as db:
        user_id = await seed(db)
        stream_fn = make_stream_agent(db, user_id)

        s1 = await chat_service.create_session(db, user_id, session_title="课3验收-1")
        await run_stream(db, stream_fn, s1.id, "我最近一周心情怎么样？", "场景 A｜日记工具（流式）")

        s2 = await chat_service.create_session(db, user_id, session_title="课3验收-2")
        await run_stream(db, stream_fn, s2.id, "考试前失眠的科学应对方法有哪些？", "场景 B｜知识库工具（流式）")

        s3 = await chat_service.create_session(db, user_id, session_title="课3验收-3")
        await run_stream(db, stream_fn, s3.id, "谢谢你陪我聊天，今天说出来好多了", "场景 C｜纯聊天（应无工具）")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    asyncio.run(main())
