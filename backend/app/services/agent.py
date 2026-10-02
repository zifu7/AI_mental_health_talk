"""Agent 对话引擎（第 2 课）：给小暖装上「工具调用 + 多轮记忆」

运行验证（backend 目录下）：venv/Scripts/python test_agent.py

设计三要点（对应讲义）：
1. 工具返回 JSON 字符串（事实），组织语言是模型的事——别替模型写句子
2. db / user_id 不进模型的参数——它们由 make_agent 在创建时注入（上下文注入）
3. 历史从库里取最近 N 条拼回 messages，让小暖"记得"之前聊过什么（治失忆）
"""
import json
import logging
from datetime import date, timedelta
from functools import partial
from collections import Counter
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.emotion_diary import EmotionDiary
from app.services import chat_service, rag
from app.utils.ai_client import trigger_emotion_analysis

logger = logging.getLogger(__name__)

# ==================== 工具定义（请求侧：说明书） ====================

# 工具 1：情绪日记统计
DIARY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_mood_summary",
        "description": "统计用户在最近 N 天里记录的情绪日记：平均心情分、出现最多的情绪、睡眠差/压力大的天数。"
                       "当用户问自己的近况回顾（心情怎么样、状态如何、最近睡得/压力如何）时调用。"
                       "用户没说具体天数时传 7。",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "往前统计多少天，1-30 之间",
                }
            },
            "required": ["days"],
        },
    },
}

# 工具 2：知识库检索
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "在平台心理健康知识库中检索与问题相关的科普资料（如失眠、焦虑、抑郁、考试压力等话题）。"
                       "当用户问的是知识/方法类问题、想要专业建议时调用，返回的资料标题和要点会帮助回答更准确。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要检索的问题或关键词，用用户原话精简",
                }
            },
            "required": ["query"],
        },
    },
}

TOOLS: List[Dict[str, Any]] = [DIARY_TOOL,SEARCH_TOOL]   

# ==================== 工具实现（响应侧：干活的函数） ====================

async def _mood_summary_impl(db: AsyncSession, user_id: int, days: int = 7) -> str:
    """统计最近 days 天的心情数据。

    注意这里故意【不返回日记原文】，只返回聚合统计：
    一是用户隐私（原文不该被模型转发展示），二是省 token——事实给数字，语言归模型。
    """
    days = max(1, min(int(days), 30))
    since = date.today() - timedelta(days=days - 1)
    stmt = (
        select(EmotionDiary)
        .where(EmotionDiary.user_id == user_id, EmotionDiary.diary_date >= since)
        .order_by(EmotionDiary.diary_date.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        return json.dumps({"count": 0, "period_days": days}, ensure_ascii=False)

    emotions = Counter(r.dominant_emotion for r in rows if r.dominant_emotion)
    return json.dumps({
        "count": len(rows),
        "period_days": days,
        "avg_mood_score": round(sum(r.mood_score for r in rows) / len(rows), 1),
        "top_emotions": [e for e, _ in emotions.most_common(2)],
        "poor_sleep_days": sum(1 for r in rows if (r.sleep_quality or 5) <= 2),
        "high_stress_days": sum(1 for r in rows if (r.stress_level or 1) >= 4),
    }, ensure_ascii=False)


async def _search_kb_impl(db: AsyncSession, query: str) -> str:
    contexts = await rag.answer_sources(db, query, top_k=3)
    results: List[Dict[str, str]] = []
    if contexts:
        for ctx in contexts:
            title = ctx.get("title", "无标题")
            content = ctx.get("content", "")
            # 1. 截断处理：超过150字加"……"
            if len(content) > 150:
                content = content[:150] + "……"
            
            # 2. 只保留 title 和 content，丢掉 score
            results.append({
                "title":title,
                "content": content
            })
    
    # 如果 contexts 为空，返回空数组，模型会知道没查到资料
    return json.dumps(results, ensure_ascii=False)


def _build_registry(db: AsyncSession, user_id: int) -> Dict[str, Callable[..., Awaitable[str]]]:
    """把请求上下文（db、user_id）绑进工具函数，返回 工具名 -> 可调用函数 的注册表。

    这是"上下文注入"：模型的参数 schema 里只有 days/query 这类业务参数，
    db 和 user_id 是服务端才知道的东西，通过 partial 预绑定，模型永远碰不到。
    """
    registry: Dict[str, Callable[..., Awaitable[str]]] = {
        "get_mood_summary": partial(_mood_summary_impl, db=db, user_id=user_id),
        # 作业：完成 _search_kb_impl 后在这里注册 "search_knowledge"
        "search_knowledge":partial(_search_kb_impl,db=db)
    }
    return registry


async def _load_history(db: AsyncSession, session_id: int, max_messages: int = 12) -> List[Dict[str, str]]:
    """把库里存的历史消息按最近的顺序拼回对话格式。

    为什么能直接拼：我们只持久化"完整回合"（用户话 + 小暖最终回答），
    工具中间轮（assistant 申请 + tool 结果）不入库，所以历史里不会出现悬空的 tool_call。
    """
    rows = await chat_service.get_messages_by_session(db, session_id)
    history: List[Dict[str, str]] = []
    for m in rows[-max_messages:]:
        role = "user" if m.sender_type == 1 else "assistant"
        if m.content:
            history.append({"role": role, "content": m.content})
    return history


async def _chat_once(messages: List[Dict[str, str]]) -> dict:
    """调一次 DeepSeek（非流式，带工具）"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": "deepseek-chat", "messages": messages, "tools": TOOLS, "stream": False},
        )
        resp.raise_for_status()
        return resp.json()


async def _run_tool(registry: Dict[str, Callable[..., Awaitable[str]]], name: str, args_str: str) -> str:
    """执行工具。任何错误都转成字符串回给模型，让它自己补救（课 1 的自愈设计）"""
    func = registry.get(name)
    if func is None:
        return f"错误：工具 {name} 不存在，请直接回答用户"
    try:
        args = json.loads(args_str) if args_str else {}
        result = await func(**args)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"工具 {name} 执行出错：{e}。请修正参数重试，或直接回答用户。"


# ==================== 系统提示词与消息组装（流式/非流式共用） ====================

SYSTEM_PROMPT = (
    "你是小暖，一位温暖专业的心理健康助手。\n"
    "你可以调用工具获取真实数据：get_mood_summary 查用户自己的情绪日记统计，"
    "search_knowledge 查心理健康知识库。工具返回的数据比你的记忆更准确，"
    "回答时要优先依据工具结果；工具没查到的信息不要编造。\n"
    "search_knowledge 返回空数组 = 平台资料里没有相关内容：要如实告诉用户"
    "“知识库里没有查到这方面的资料”，可以再给一句温和的方向性建议，"
    "但绝不能编造资料或伪造引用；涉及用药、诊断的问题一律建议去正规医院咨询医生。\n"
    "调用工具前用一句简短的中文说明你在做什么，不要输出英文。\n"
    "用户问近况（心情/状态/睡眠/压力）时用日记工具，问知识方法类问题时用知识库工具；"
    "能直接共情回答的就不用工具，不要为了调而调。"
)

# 工具名 -> 前端展示文案（工具执行时推给用户的"人话"）
TOOL_LABELS = {
    "get_mood_summary": "正在查看你的情绪日记",
    "search_knowledge": "正在检索知识库",
}


async def _build_messages(db: AsyncSession, session_id: int, user_message: str) -> List[Dict[str, Any]]:
    """组装一轮对话的完整 messages：系统提示 + 历史记忆 + 本次用户消息"""
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += await _load_history(db, session_id)
    messages.append({"role": "user", "content": user_message})
    return messages


# ==================== 引擎：请求级工厂 ====================

def make_agent(db: AsyncSession, user_id: int):
    """每个请求创建一次：绑定 db 和 user_id，返回 agent_chat(session_id, user_message)。

    为什么是"工厂 + 闭包"而不是全局函数：db 会话和当前用户是请求级的，
    全局单例会把 A 用户的会话串到 B 用户头上（多用户系统的大忌）。
    """
    registry = _build_registry(db, user_id)

    async def agent_chat(session_id: int, user_message: str) -> str:
        messages = await _build_messages(db, session_id, user_message)

        for _ in range(3):                                   # 防死循环护栏
            reply = await _chat_once(messages)
            msg = reply["choices"][0]["message"]

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                return msg.get("content") or "（模型没有输出内容）"

            # 原样回传 assistant 申请，再按 id 一一回传工具结果（课 1 协议）
            messages.append(msg)
            for tc in tool_calls:
                result = await _run_tool(registry, tc["function"]["name"], tc["function"]["arguments"])
                logger.info("工具执行: %s -> %s", tc["function"]["name"], result[:100])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        return "（超过 3 轮工具循环，已截断——请换个说法重问）"

    return agent_chat


# ==================== 流式引擎（第 3 课） ====================

async def _stream_chat_once(messages: List[Dict[str, Any]]) -> AsyncGenerator[Tuple[str, Any], None]:
    """流式调用一轮模型：边把正文吐给调用方，边把 tool_calls 分片攒完整。

    yield 两类事件（Python 元组）：
      ("content", "文字片段") —— 正文增量，调用方立刻转发给用户
      ("result",  {...})      —— 本轮结束汇总：content / tool_calls / finish_reason

    为什么非要"攒"：流式下 tool_calls 是分片到达的（先给 id 和函数名，
    再一小段一小段地吐 arguments 字符串）。课 1 为了避开这堆解析，工具轮直接
    用了非流式；代价是模型的前导句（"让我查一下你的近况"）也要憋到最后才出现。
    生产环境要体验，只能把这些分片按 index 拼回来——index 是"同时申请的第几个工具"。
    """
    full_content = ""
    tool_calls_acc: Dict[int, Dict[str, Any]] = {}
    finish_reason = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": "deepseek-chat", "messages": messages, "tools": TOOLS, "stream": True},
        ) as resp:
            if resp.status_code != 200:
                yield ("error", f"AI服务异常: {resp.status_code}")
                return

            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choice = chunk["choices"][0]
                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]
                delta = choice.get("delta") or {}

                # ① 正文增量：立刻转发
                if delta.get("content"):
                    full_content += delta["content"]
                    yield ("content", delta["content"])

                # ② 工具调用分片：按 index 拼装（id 只来一次；arguments 必须累加）
                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    slot = tool_calls_acc.setdefault(
                        idx, {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                    )
                    if tc.get("id"):
                        slot["id"] = tc["id"]
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        slot["function"]["name"] = fn["name"]      # 实测：名字只在首个分片出现
                    if fn.get("arguments"):
                        slot["function"]["arguments"] += fn["arguments"]

    tool_calls = [tool_calls_acc[i] for i in sorted(tool_calls_acc)] or None
    yield ("result", {"content": full_content, "tool_calls": tool_calls, "finish_reason": finish_reason})


def make_stream_agent(db: AsyncSession, user_id: int):
    """流式版引擎：与 make_agent 同源（同一套提示词、注册表、历史组装），
    区别只在"边生成边发"。返回 stream_agent_chat(session_id, user_message)。

    产出的是 SSE 字符串，事件协议（前端的接口契约）：
      data:      {"code":200,"data":{"content":"片段"}}   正文增量（沿用旧格式，前端不用改）
      event:tool {"name","label","status"}                工具执行状态（running/done，新增）
      event:done {"content":"完整回答"}                    结束（沿用旧格式）
      event:error{"message":"..."}                        出错（沿用旧格式）
    """
    registry = _build_registry(db, user_id)

    async def stream_agent_chat(session_id: int, user_message: str) -> AsyncGenerator[str, None]:
        messages = await _build_messages(db, session_id, user_message)
        full_answer = ""

        for _ in range(3):                                   # 防死循环护栏
            result: Dict[str, Any] = {}
            async for kind, payload in _stream_chat_once(messages):
                if kind == "content":
                    full_answer += payload
                    yield f"data: {json.dumps({'code': 200, 'data': {'content': payload}})}\n\n"
                elif kind == "error":
                    yield f"event: error\ndata: {json.dumps({'message': payload})}\n\n"
                    return
                else:
                    result = payload

            tool_calls = result.get("tool_calls")
            if not tool_calls:
                # 没有工具申请 = 这轮正文就是最终回答
                await chat_service.add_message(db, session_id, sender_type=2, content=full_answer)
                await trigger_emotion_analysis(db, session_id)   # 沿用旧链路的情绪分析
                yield f"event: done\ndata: {json.dumps({'content': full_answer})}\n\n"
                return

            # 原样回传 assistant 申请（协议要求）；content 也带上——前导句可能已经流给用户了
            messages.append({"role": "assistant", "content": result.get("content", ""), "tool_calls": tool_calls})

            for tc in tool_calls:
                name = tc["function"]["name"]
                label = TOOL_LABELS.get(name, name)
                # 先告诉用户"小暖正在干什么"，再干活——消灭白屏等待
                yield f"event: tool\ndata: {json.dumps({'name': name, 'label': label, 'status': 'running'})}\n\n"
                tool_result = await _run_tool(registry, name, tc["function"]["arguments"])
                yield f"event: tool\ndata: {json.dumps({'name': name, 'label': label, 'status': 'done'})}\n\n"
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": tool_result})

        # 超轮兜底：已经流给用户的内容也存下来，别让这一轮凭空消失
        await chat_service.add_message(
            db, session_id, sender_type=2,
            content=full_answer or "（本轮工具调用超限，请换个说法再问一次）",
        )
        yield f"event: done\ndata: {json.dumps({'content': full_answer})}\n\n"

    return stream_agent_chat
