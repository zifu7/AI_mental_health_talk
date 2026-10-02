import json
import logging
import httpx
import asyncio
import re
from typing import AsyncGenerator, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services import chat_service

logger = logging.getLogger(__name__)

# 模拟模式开关（True=使用模拟回复，不消耗 API）
USE_MOCK = False   # 有真实 API Key 时改为 False


async def stream_deepseek(session_id: int, user_message: str, db: AsyncSession) -> AsyncGenerator[str, None]:
    """流式生成 AI 回复，结束后自动触发情绪分析"""
    try:
        if USE_MOCK:
            mock_response = f"你好！我是小暖。我收到了你的消息：『{user_message}』。这是模拟回复（未接入真实 API）。"
            # 逐字发送
            for char in mock_response:
                yield f"data: {json.dumps({'code': 200, 'data': {'content': char}})}\n\n"
                await asyncio.sleep(0.03)
            # 保存 AI 消息
            await chat_service.add_message(db, session_id, sender_type=2, content=mock_response)
            # 触发情绪分析
            await trigger_emotion_analysis(db, session_id)
            yield f"event: done\ndata: {json.dumps({'content': mock_response})}\n\n"
            return

        # ===== 真实 DeepSeek API =====
        messages = [
            {"role": "system", "content": "你是一位温暖的心理健康助手，你的名字叫小暖。"},
            {"role": "user", "content": user_message}
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"event: error\ndata: {json.dumps({'message': f'AI服务异常: {response.status_code}'})}\n\n"
                    return

                full_content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            # 保存 AI 完整回复
                            await chat_service.add_message(db, session_id, sender_type=2, content=full_content)

                            # 触发情绪分析
                            await trigger_emotion_analysis(db, session_id)
                            # 发送完成事件
                            yield f"event: done\ndata: {json.dumps({'content': full_content})}\n\n"
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                yield f"data: {json.dumps({'code': 200, 'data': {'content': content}})}\n\n"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': f'服务器错误: {str(e)}'})}\n\n"


async def trigger_emotion_analysis(db: AsyncSession, session_id: int):
    """在后台执行情绪分析，不阻塞主流程"""
    try:
        # 1. 获取会话所有消息
        messages = await chat_service.get_messages_by_session(db, session_id)
        if not messages:
            return
        # 2. 构造 AI 所需格式
        history = []
        for msg in messages:
            role = "user" if msg.sender_type == 1 else "assistant"
            history.append({"role": role, "content": msg.content})
        # 3. 调用分析
        analysis = await analyze_session_emotion(history)
        # 4. 存储结果
        await chat_service.update_session_emotion(db, session_id, analysis)
    except Exception as e:
        logger.exception("情绪分析失败, session_id=%s: %s", session_id, e)


async def analyze_session_emotion(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """调用 DeepSeek 分析情绪，若模拟模式或无 API Key 则返回模拟数据"""
    # 模拟模式或没有 API Key，返回默认数据
    if USE_MOCK or not settings.DEEPSEEK_API_KEY:
        return {
            "primaryEmotion": "平静",
            "emotionScore": 60,
            "isNegative": False,
            "riskLevel": 1,
            "suggestion": "情绪状态平稳，继续保持",
            "improvementSuggestions": ["多与朋友交流", "保持规律作息"],
            "riskDescription": ""
        }

    system_prompt = """
你是一位情绪分析专家。请分析以下对话中用户的情绪状态，并以 JSON 格式返回结果，字段如下：
- primaryEmotion: 主要情绪（如：快乐、焦虑、悲伤、平静、愤怒、恐惧、失望、困惑、兴奋、疲惫）
- emotionScore: 情绪积极程度（0-100，数值越高越积极）
- isNegative: 是否负面情绪（true/false）
- riskLevel: 风险等级（1=正常, 2=关注, 3=预警, 4=危机）
- suggestion: 给用户的简短建议（一句话，不超过50字）
- improvementSuggestions: 改善建议列表（最多3条，每条不超过20字）
- riskDescription: 风险描述（如果 riskLevel>1，说明具体风险，否则为""）

只返回 JSON，不要其他文字。
"""
    messages_for_ai = [{"role": "system", "content": system_prompt}] + messages

    payload = {
        "model": "deepseek-chat",
        "messages": messages_for_ai,
        "temperature": 0.3,
        "stream": False,
        # JSON 模式：让接口层保证返回值是合法 JSON，比"模型自愿输出 JSON + 正则抠"可靠得多
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        # 兼容不支持 response_format 的 OpenAI 兼容端（部分中转服务会直接 400）：
        # 摘掉该参数重试一次，而不是让整条情绪分析链路挂掉。
        if response.status_code == 400:
            logger.warning("response_format 被拒绝(400)，降级为普通模式重试: %s", response.text[:200])
            payload.pop("response_format", None)
            response = await client.post(
                f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
        if response.status_code != 200:
            raise Exception(f"AI 分析失败: {response.status_code}")

        content = response.json()["choices"][0]["message"]["content"]
        return _parse_analysis_json(content)


def _parse_analysis_json(content: str) -> Dict[str, Any]:
    """解析情绪分析结果。

    首选直接 json.loads——开了 json_object 模式后返回值就是纯 JSON。
    兜底再用正则抠第一个 {...}：服务端不支持 JSON 模式时，模型可能把 JSON
    裹在 ``` 代码块或解释文字里，正则能救回来。
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise Exception("AI 返回格式异常")
        return json.loads(json_match.group())


async def stream_knowledge_qa(
    session_id: int,
    user_message: str,
    db: AsyncSession,
    contexts: List[Dict[str, Any]],
) -> AsyncGenerator[str, None]:
    """知识库问答（RAG）流式回复

    和 stream_deepseek 的区别：
      1. system prompt 换成检索资料拼成的提示词（带引用编号规则）
      2. 结束时在回答末尾追加"参考资料"列表，随内容一起存库
      3. 不触发情绪分析（这是知识问答，不是情绪倾诉）
    """
    from app.services.rag import build_prompt, format_citations

    messages = [
        {"role": "system", "content": build_prompt(user_message, contexts)},
        {"role": "user", "content": user_message},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": "deepseek-chat", "messages": messages, "stream": True},
        ) as response:
            if response.status_code != 200:
                yield f"event: error\ndata: {json.dumps({'message': f'AI服务异常: {response.status_code}'})}\n\n"
                return

            full_content = ""
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    # 先拼参考资料再存库（客户端中途断开也不丢完整内容）
                    citations_text = format_citations(contexts)
                    full_content += citations_text
                    await chat_service.add_message(db, session_id, sender_type=2, content=full_content)
                    # 参考资料作为普通内容片段推给前端
                    for i in range(0, len(citations_text), 50):
                        yield f"data: {json.dumps({'code': 200, 'data': {'content': citations_text[i:i + 50]}})}\n\n"
                    yield f"event: done\ndata: {json.dumps({'content': full_content})}\n\n"
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_content += content
                        yield f"data: {json.dumps({'code': 200, 'data': {'content': content}})}\n\n"
                except json.JSONDecodeError:
                    continue
