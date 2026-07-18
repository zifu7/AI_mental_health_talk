import json
import httpx
import asyncio
import re
from typing import AsyncGenerator, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services import chat_service

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
        print(f"❌ 情绪分析失败: {e}")


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

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages_for_ai,
                "temperature": 0.3,
                "stream": False
            }
        )
        if response.status_code != 200:
            raise Exception(f"AI 分析失败: {response.status_code}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # 提取 JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise Exception("AI 返回格式异常")
        return json.loads(json_match.group())