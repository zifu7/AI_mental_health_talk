<template>
  <div class="consultation-container">
    <div class="sidebar">
      <!-- AI助手信息 -->
      <div class="ai-assistant-info">
        <div class="breathing-circle">
          <el-image
            :src="aiAvatarIcon"
            alt="AI助手图标"
            style="width: 25px; height: 25px"
          />
        </div>
        <h3 class="assistant-name">宁渡AI助手</h3>
        <div class="online-status">
          <div class="status-dot"></div>
          在线服务中
        </div>
      </div>
      <!-- 情绪花园 -->
      <div class="emotion-garden">
        <div class="emotion-header">
          <div class="emotion-title">情绪花园</div>
        </div>
        <div class="emotion-info">
          <div class="emotion-name">中性</div>
          <div class="emotion-score">50</div>
        </div>
        <div class="warm-tips">
          <div class="emotion-status-text">
            <span class="status-label">今天感觉</span>
            <span class="status-emotion">{{
              currentEmotion.isNegative ? "需要关注" : "很不错"
            }}</span>
          </div>
          <div class="emotion-intensity">
            <span class="intensity-dots">
              <span
                v-for="dot in 3"
                :key="dot"
                class="dot"
                :class="{
                  active: getIntensityClass(currentEmotion.emotionScore) >= dot,
                }"
              ></span>
            </span>
            <span class="intensity-text">{{
              getRiskText(currentEmotion.riskLevel)
            }}</span>
          </div>
          <!-- 温暖建议卡片 -->
          <div class="warm-suggestion" v-if="currentEmotion.suggestion">
            <div class="suggestion-icon">💝</div>
            <div class="suggestion-content">
              <div class="suggestion-title">给你的小建议</div>
              <div class="suggestion-text">{{ currentEmotion.suggestion }}</div>
            </div>
          </div>
          <!-- 治愈行动 -->
          <div
            class="healing-actions"
            v-if="currentEmotion.healingActions.length > 0"
          >
            <div class="actions-title">治愈小行动</div>
            <div class="actions-list">
              <div
                v-for="action in currentEmotion.healingActions"
                :key="action"
                class="action-item"
              >
                <div class="action-icon">✨</div>
                <div class="action-text">{{ action }}</div>
              </div>
            </div>
          </div>
          <!-- 风险提示 -->
          <div
            class="risk-notice"
            v-if="currentEmotion.isNegative && currentEmotion.riskLevel > 1"
          >
            <div class="notice-icon">🤗</div>
            <div class="notice-content">
              <div class="notice-title">温馨提示</div>
              <div class="notice-text">
                {{ currentEmotion.riskDescription }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 会话列表 -->
      <div class="session-history">
        <h4 class="section-title">会话列表</h4>
        <div class="session-list">
          <div
            v-for="session in sessionList"
            :key="session.id"
            class="session-item"
            @click="selectSession(session.id)"
          >
            <div class="session-info">
              <div class="session-title">
                <span>{{ session.sessionTitle }}</span>
                <div class="session-meta">
                  <span class="session-time">{{ session.startedAt }}</span>
                </div>
                <div class="session-preview">
                  {{ session.lastMessageContent }}
                </div>
                <div class="session-stats">
                  <span>
                    <el-icon>
                      <ChatRound />
                    </el-icon>
                    {{ session.messageCount || 0 }}
                  </span>
                  <span>
                    <el-icon>
                      <Clock />
                    </el-icon>
                    {{ session.durationMinutes || 0 }}分钟
                  </span>
                </div>
              </div>
              <div class="session-actions">
                <el-button
                  text
                  type="danger"
                  size="mini"
                  @click="handleDelete(session.id)"
                >
                  <el-icon>
                    <DeleteFilled />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-main">
      <div class="chat-header">
        <div class="header-left">
          <div class="chat-avatar">
            <el-image
              :src="userAvatarIcon"
              alt="用户头像"
              style="width: 30px; height: 30px"
            />
          </div>
          <div class="chat-info">
            <h2>宁渡AI助手</h2>
            <p>您的贴心AI心理健康助手</p>
          </div>
        </div>
        <el-button circle @click="createTempSession" title="创建新会话">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <!-- 聊天消息区域 -->
      <div class="chat-messages">
        <div class="message-item ai-message" v-if="messageDetail.length === 0">
          <div class="message-avatar">
            <el-image
              :src="aiAvatarIcon"
              alt="AI助手图标"
              style="width: 18px; height: 18px"
            />
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <p>
                您好！我是小暖，您的心理健康心理健康助手。很高兴陪伴您，为您提供温暖的心理支持。今天您感觉怎么样？有什么要分享的吗？
              </p>
            </div>
            <div class="message-time">刚刚</div>
          </div>
        </div>
        <div
          v-for="msg in messageDetail"
          :key="msg.id"
          class="message-item"
          :class="msg.senderType === 2 ? 'ai-message' : 'user-message'"
        >
          <div class="message-avatar">
            <el-image
              v-if="msg.senderType === 2"
              :src="aiAvatarIcon"
              style="width: 18px; height: 18px"
              alt="AI助手图标"
            />
            <el-image
              v-else
              :src="users"
              alt="用户头像"
              style="width: 18px; height: 18px"
            />
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <!-- AI正在思考中 -->
              <div
                v-if="msg.senderType === 2 && !msg.content"
                class="typing-indicator"
              >
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
              </div>
              <!-- AI错误提示 -->
              <div v-else-if="msg.isError" class="error-message">
                <p>{{ msg.content }}</p>
              </div>
              <!-- AI正常返回消息 -->
              <MarkdownRenderer
                v-else-if="msg.senderType === 2 && !msg.isError"
                :content="msg.content"
                :is-ai-message="true"
              />
              <p
                v-else-if="msg.content"
                v-html="formatMessage(msg.content)"
              ></p>
            </div>

            <div class="message-time">
              {{
                msg.senderType === 2 && isAiResponding
                  ? "正在输入中..."
                  : msg.createdAt
              }}
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <div class="input-container">
          <el-input
            v-model="inputContent"
            placeholder="请输入您想要分享的内容..."
            type="textarea"
            :rows="3"
            :disabled="isAiResponding"
            @keydown="handleInputKeydown"
            class="message-input"
            clearable
          ></el-input>
          <div class="input-footer">
            <span>按enter发送，按shift+enter换行</span>
            <span>{{ inputContent.length }}/500</span>
          </div>
        </div>
        <el-button
          :disabled="inputContent.length === 0 || inputContent.length > 500"
          class="send-btn"
          type="primary"
          @click="handleSendMessage"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import MarkdownRenderer from "@/components/MarkdownRenderer.vue";
import {
  startSession,
  getSessionList,
  deleteSession,
  getSessionDetail,
  getEmotionAnalysis,
} from "@/api/frontend";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import {
  ChatRound,
  Clock,
  DeleteFilled,
  Plus,
  Promotion,
} from "@element-plus/icons-vue";

// 图标资源
const aiAvatarIcon = new URL("@/assets/images/1.png", import.meta.url).href;
const userAvatarIcon = new URL("@/assets/images/2.png", import.meta.url).href;
const users = new URL("@/assets/images/13.png", import.meta.url).href;

// 响应式数据
const inputContent = ref("");
const isAiResponding = ref(false);
const activeSession = ref(null);
const sessionList = ref([]);
const messageDetail = ref([]);
//情绪花园
const currentEmotion = ref({
  primaryEmotion: "中性",
  emotionScore: 50,
  isNegative: false,
  riskLevel: 1,
  suggestion: "情绪状态平稳",
  healingActions: [],
  riskDescription: "",
});
// 获取情绪强度类名
const getIntensityClass = (score) => {
  if (score >= 61) return 3;
  else if (score >= 31) return 2;
  else return 1;
};

const getRiskText = (level) => {
  switch (level) {
    case 1:
      return "正常";
    case 2:
      return "关注";
    case 3:
      return "预警";
    case 4:
      return "危机";
    default:
      return "正常";
  }
};

// 获取情绪分析结果
const getEmotionAnalysisData = async (sessionId) => {
  if (!sessionId) return;
  const id = sessionId.toString().startsWith("session_")
    ? sessionId
    : "session_" + sessionId;
  try {
    const res = await getEmotionAnalysis(id);
    if (res && res.data) {
      // 合并返回数据，保留默认值中可能缺失的字段
      currentEmotion.value = {
        ...currentEmotion.value,
        ...res.data,
      };
    }
  } catch (err) {
    console.error("获取情绪分析失败:", err);
    ElMessage.error("获取情绪分析结果失败，请重试");
  }
};

// ---------- 创建临时会话 ----------
const createTempSession = () => {
  const tempSession = {
    sessionId: `temp-${Date.now()}`,
    status: "TEMP",
    sessionTitle: "新会话",
  };
  activeSession.value = tempSession;
  // 清空当前消息列表（可选）
  messageDetail.value = [];
};

// ---------- 升级临时会话为正式会话 ----------
const upgradeTempSession = async (firstUserMessage) => {
  const sessionCreateParams = {
    initialMessage: firstUserMessage || "你好",
  };
  if (activeSession.value.sessionTitle === "新会话") {
    sessionCreateParams.sessionTitle = `宁渡AI助手 - ${new Date().toLocaleString()}`;
  } else {
    sessionCreateParams.sessionTitle = activeSession.value.sessionTitle;
  }
  try {
    const res = await startSession(sessionCreateParams);
    const sessionData = {
      sessionId: res.sessionId,
      status: res.status,
      sessionTitle: sessionCreateParams.sessionTitle,
    };
    activeSession.value = sessionData;
  } catch (err) {
    console.error("升级会话失败:", err);
    ElMessage.error("创建会话失败，请重试");
    throw err; // 向上抛出，让调用方感知
  }
};

// ---------- 发送消息 ----------
const handleSendMessage = async () => {
  if (!inputContent.value.trim()) return;
  if (isAiResponding.value) return;

  const userText = inputContent.value.trim();
  inputContent.value = "";

  // 1. 添加用户消息
  messageDetail.value.push({
    id: `user-${Date.now()}`,
    senderType: 1,
    content: userText,
    createdAt: new Date().toLocaleString(),
  });

  // 2. 如果是临时会话，先升级（等待完成）
  if (activeSession.value.status === "TEMP") {
    try {
      await upgradeTempSession(userText);
    } catch (e) {
      // 升级失败，不再继续发送
      return;
    }
  } else {
    //继续现有会话对话
  }

  // 3. 更新会话列表（后台刷新）
  getSessionPage();

  // 4. 发起流式对话
  startStreaming(activeSession.value.sessionId, userText);
};

// ---------- 流式对话 ----------
const startStreaming = async (sessionId, userText) => {
  if (isAiResponding.value) {
    ElMessage.warning("AI助手正在回复中，请稍后再发送");
    return;
  }

  isAiResponding.value = true;

  // 创建 AI 消息占位
  const aiMsg = {
    id: `ai-${Date.now()}-${Math.random().toString(36).substring(2)}`,
    senderType: 2,
    content: "",
    createdAt: new Date().toLocaleString(),
    isError: false,
  };
  messageDetail.value.push(aiMsg);

  const ctrl = new AbortController();

  // 错误处理函数（内部使用）
  const handleError = (errorMsg) => {
    const lastMsg = messageDetail.value[messageDetail.value.length - 1];
    if (lastMsg && lastMsg.senderType === 2) {
      lastMsg.content = "❌ " + errorMsg;
      lastMsg.isError = true;
    }
    isAiResponding.value = false;
    ElMessage.error(errorMsg);
  };

  fetchEventSource("/api/psychological-chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      token: localStorage.getItem("token"),
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      sessionId,
      userMessageText: userText, // 根据后端实际字段名调整
    }),
    signal: ctrl.signal,
    onopen: async (response) => {
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        handleError(
          `服务器响应异常 (${response.status}): ${text.substring(0, 100)}`,
        );
        ctrl.abort();
        return;
      }
      const contentType = response.headers.get("Content-Type");
      if (contentType !== "text/event-stream") {
        handleError(`服务器返回非流式数据 (${contentType})`);
        ctrl.abort();
      }
    },
    onmessage: (event) => {
      const raw = event.data.trim();
      if (!raw) return;

      const eventName = event.name;
      const lastMsg = messageDetail.value[messageDetail.value.length - 1];

      // 专门处理 error 事件
      if (eventName === "error") {
        try {
          const payload = JSON.parse(raw);
          // 兼容 msg 和 message 字段
          const errMsg = payload.msg || payload.message || "AI服务异常";
          handleError(errMsg);
        } catch {
          handleError("AI服务异常");
        }
        ctrl.abort();
        getEmotionAnalysisData(sessionId);
        return;
      }

      if (eventName === "done") {
        if (raw) {
          lastMsg.content = raw;
        }
        isAiResponding.value = false;
        ctrl.abort();
        return;
      }

      // 正常数据流（假设为 JSON 格式）
      try {
        const payload = JSON.parse(raw);
        if (payload.code === 200 && payload.data?.content) {
          // 增量更新 AI 消息内容
          lastMsg.content = payload.data.content;
        } else {
          // 兼容不同错误字段
          const errMsg = payload.msg || payload.message || "未知错误";
          handleError(errMsg);
          ctrl.abort();
        }
      } catch (e) {
        handleError("解析响应数据失败");
        ctrl.abort();
      }
    },
    onerror: (error) => {
      console.error("SSE onerror:", error);
      handleError(error.message || "网络错误");
      ctrl.abort();
      // 不抛出，避免未捕获
    },
    onclose: () => {
      getEmotionAnalysisData(sessionId);
    },
  });
};

// ---------- 键盘事件 ----------
const handleInputKeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSendMessage();
  }
};

// ---------- 获取会话列表 ----------
const getSessionPage = async () => {
  try {
    const res = await getSessionList({
      pageNum: 1,
      pageSize: 10,
    });
    sessionList.value = res.records || [];
  } catch (err) {
    console.error("获取会话列表失败:", err);
  }
};

// ---------- 获取会话详情 ----------
const selectSession = async (sessionId) => {
  try {
    const res = await getSessionDetail(sessionId);
    messageDetail.value = res || [];
    activeSession.value = { sessionId, ...res };
    // 获取情绪分析结果
    getEmotionAnalysisData(sessionId);
  } catch (err) {
    console.error("获取会话详情失败:", err);
    ElMessage.error("加载会话失败");
  }
};

// ---------- 删除会话 ----------
const handleDelete = async (sessionId) => {
  try {
    await deleteSession(sessionId);
    ElMessage.success("删除成功");
    getSessionPage();
    // 如果删除的是当前会话，清空消息
    if (activeSession.value?.sessionId === sessionId) {
      activeSession.value = null;
      messageDetail.value = [];
      createTempSession();
    }
  } catch (err) {
    console.error("删除会话失败:", err);
    ElMessage.error("删除失败");
  }
};

// ---------- 格式化消息（换行） ----------
const formatMessage = (message) => {
  if (!message) return "";
  return message.replace(/\n/g, "<br>");
};

// ---------- 生命周期 ----------
onMounted(() => {
  getSessionPage();
  createTempSession();
});
</script>

<style lang="scss" scoped>
.consultation-container {
  margin: 0 auto;
  width: 1200px;
  display: flex;
  gap: 20px;
  padding: 20px;
  .sidebar {
    width: 320px;
    .ai-assistant-info {
      margin-bottom: 20px;
      background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(255, 252, 248, 0.95) 100%
      );
      border-radius: 16px;
      padding: 16px;
      box-shadow:
        0 8px 32px rgba(251, 146, 60, 0.06),
        0 2px 8px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(251, 146, 60, 0.08);
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
      .breathing-circle {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #fb923c 0%, #f59e0b 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        animation: breathing 4s ease-in-out infinite;
        box-shadow: 0 6px 24px rgba(251, 146, 60, 0.25);
        position: relative;
      }
      .assistant-name {
        font-size: 16px;
        font-weight: 700;
        background: linear-gradient(135deg, #fb923c, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        background-clip: text;
        margin: 0 0 12px;
      }
      .online-status {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #059669;
        font-size: 12px;
        font-weight: 600;
        .status-dot {
          width: 8px;
          height: 8px;
          background: #059669;
          border-radius: 50%;
          margin-right: 8px;
          animation: pulse 2s infinite;
          box-shadow: 0 0 8px rgba(5, 150, 105, 0.4);
        }
      }
    }
    .session-history {
      background: white;
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      margin-bottom: 20px;
      min-height: 250px;
      display: flex;
      flex-direction: column;
      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin: 0 0 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .session-list {
        overflow-y: auto;
        max-height: 200px;
        scrollbar-width: thin;
        scrollbar-color: rgba(64, 150, 255, 0.3) transparent;
        .session-item {
          position: relative;
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px;
          margin-bottom: 8px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          border: 2px solid transparent;
          &:hover {
            background: #f8f9ff;
            border-color: #e6f0ff;
          }
          &.active {
            background: #e6f0ff;
            border-color: #4096ff;
          }
          .session-info {
            flex: 1;
            .session-title {
              font-weight: 500;
              font-size: 14px;
              color: #333;
              margin-bottom: 4px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              .session-meta {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 6px;
                .session-time {
                  font-size: 12px;
                  color: #999;
                }
              }
              .session-preview {
                width: 200px;
                font-size: 12px;
                color: #666;
                margin-bottom: 6px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
              }
              .session-stats {
                display: flex;
                align-items: center;
                gap: 12px;
                span {
                  font-size: 12px;
                  color: #999;
                  display: flex;
                  align-items: center;
                  gap: 4px;
                }
              }
            }
            .session-actions {
              position: absolute;
              top: 10px;
              right: 12px;
            }
          }
        }
        .no-sessions-text {
          text-align: center;
          font-size: 14px;
          color: #999;
        }
      }
    }
    .emotion-garden {
      background: linear-gradient(
        135deg,
        #fef9e7 0%,
        #fcf4e6 50%,
        #f6f0e8 100%
      );
      border-radius: 20px;
      padding: 16px;
      margin-bottom: 20px;
      box-shadow: 0 8px 32px rgba(252, 244, 230, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.2);
      position: relative;
      overflow: hidden;
      min-height: 300px;

      .garden-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        position: relative;
        z-index: 2;
        .garden-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 16px;
          font-weight: 600;
          color: #8b4513;
        }
      }
      .emotion-info {
        margin: 0 auto;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 10;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.8);
        background: linear-gradient(
          135deg,
          #ff9a9e 0%,
          #fecfef 50%,
          #fecfef 100%
        );
        color: #fff;
        .emotion-name {
          font-size: 15px;
          font-weight: 600;
          line-height: 1;
          margin-bottom: 2px;
        }
        .emotion-score {
          font-size: 14px;
          font-weight: 700;
          opacity: 0.9;
        }
      }
      .warm-tips {
        text-align: center;
        margin-bottom: 16px;
        .emotion-status-text {
          margin-bottom: 12px;
          .status-label {
            font-size: 14px;
            color: #8b7355;
            margin-right: 8px;
          }
          .status-emotion {
            font-size: 16px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 16px;
            display: inline-block;
          }
        }
        .emotion-intensity {
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          .intensity-dots {
            display: flex;
            gap: 4px;
            .dot {
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: #e0e0e0;
              transition: all 0.3s ease;
              &.active {
                background: linear-gradient(135deg, #ff9a9e, #fecfef);
                transform: scale(1.2);
                box-shadow: 0 2px 8px rgba(255, 154, 158, 0.4);
              }
            }
          }
          .intensity-text {
            font-size: 12px;
            color: #8b7355;
            font-weight: 500;
          }
        }
        .warm-suggestion {
          background: linear-gradient(
            135deg,
            rgba(255, 255, 255, 0.95),
            rgba(255, 255, 255, 0.8)
          );
          border-radius: 16px;
          padding: 12px;
          margin-bottom: 16px;
          display: flex;
          align-items: flex-start;
          gap: 10px;
          border: 1px solid rgba(255, 255, 255, 0.6);
          box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
          .suggestion-icon {
            font-size: 20px;
            flex-shrink: 0;
            margin-top: 2px;
          }
          .suggestion-content {
            text-align: left;
            flex: 1;
            .suggestion-title {
              font-size: 14px;
              font-weight: 600;
              color: #8b7355;
              margin-bottom: 6px;
            }
            .suggestion-text {
              font-size: 13px;
              color: #6b5b47;
              line-height: 1.5;
            }
          }
        }
        .healing-actions {
          margin-bottom: 16px;
          .actions-title {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 600;
            color: #8b7355;
            margin-bottom: 16px;
          }
          .actions-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            .action-item {
              background: linear-gradient(
                135deg,
                rgba(255, 255, 255, 0.9),
                rgba(255, 255, 255, 0.7)
              );
              border-radius: 12px;
              padding: 12px;
              display: flex;
              align-items: center;
              gap: 10px;
              border: 1px solid rgba(255, 255, 255, 0.5);
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
              text-align: left;
              .action-icon {
                font-size: 14px;
                color: #ffd700;
                flex-shrink: 0;
              }
              .action-text {
                font-size: 12px;
                color: #6b5b47;
                line-height: 1.4;
                flex: 1;
              }
            }
          }
        }
        .risk-notice {
          background: linear-gradient(135deg, #fff9e6, #ffeaa7);
          border-radius: 16px;
          padding: 16px;
          display: flex;
          align-items: flex-start;
          gap: 12px;
          border: 1px solid rgba(255, 234, 167, 0.6);
          box-shadow: 0 6px 20px rgba(255, 234, 167, 0.3);
          .notice-icon {
            font-size: 20px;
            flex-shrink: 0;
            margin-top: 2px;
          }
          .notice-content {
            flex: 1;
            .notice-title {
              font-size: 14px;
              font-weight: 600;
              color: #d4840f;
              margin-bottom: 6px;
            }
            .notice-text {
              font-size: 13px;
              color: #b8740c;
              line-height: 1.5;
            }
          }
        }
      }
    }
  }
  .chat-main {
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 252, 250, 0.98) 100%
    );
    border-radius: 20px;
    box-shadow:
      0 12px 40px rgba(251, 146, 60, 0.08),
      0 4px 16px rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(251, 146, 60, 0.1);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex: 1;
    .chat-header {
      background: linear-gradient(135deg, #fb923c 0%, #f59e0b 100%);
      color: white;
      padding: 20px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
      flex-shrink: 0;
      .header-left {
        display: flex;
        align-items: center;
        .chat-avatar {
          width: 48px;
          height: 48px;
          background: rgba(255, 255, 255, 0.25);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          position: relative;
          z-index: 1;
        }
        .chat-info {
          h2 {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
          }
          p {
            font-size: 14px;
          }
        }
      }
    }
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.02) 0%,
        rgba(255, 252, 248, 0.05) 100%
      );
      min-height: 0;
      max-height: calc(100vh - 200px);
      scrollbar-width: thin;
      scrollbar-color: rgba(251, 146, 60, 0.3) transparent;
      .message-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          color: white;
          flex-shrink: 0;
        }
        &.ai-message {
          .message-avatar {
            background: linear-gradient(135deg, #fb923c, #f59e0b);
            box-shadow: 0 4px 12px rgba(251, 146, 60, 0.3);
          }
        }
        &.user-message {
          .message-avatar {
            background: linear-gradient(135deg, #6b7280, #4b5563);
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
          }
        }
        .message-content {
          max-width: 70%;
          .message-bubble {
            background: linear-gradient(
              135deg,
              rgba(255, 255, 255, 0.9) 0%,
              rgba(255, 252, 248, 0.95) 100%
            );
            border-radius: 16px;
            padding: 12px 16px;
            position: relative;
            animation: fadeInUp 0.4s ease-out;
            border: 1px solid rgba(251, 146, 60, 0.1);
            box-shadow: 0 4px 16px rgba(251, 146, 60, 0.05);
            .typing-indicator {
              display: flex;
              gap: 4px;
              padding: 8px 0;
              .typing-dot {
                width: 8px;
                height: 8px;
                background: #ccc;
                border-radius: 50%;
                animation: typing 1.5s ease-in-out infinite;
                &:nth-child(2) {
                  animation-delay: 0.2s;
                }
                &:nth-child(3) {
                  animation-delay: 0.4s;
                }
              }
            }
            /* 错误消息样式 */
            .error-message {
              background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
              border: 1px solid #f87171;
              border-radius: 12px;
              padding: 12px 16px;
              color: #991b1b;
              font-weight: 500;
              display: flex;
              align-items: center;
              gap: 8px;
            }
          }
          .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
          }
        }
      }
    }
    .chat-input {
      border-top: 1px solid rgba(251, 146, 60, 0.1);
      padding: 20px 24px;
      display: flex;
      gap: 12px;
      align-items: flex-end;
      background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.5) 0%,
        rgba(255, 252, 248, 0.7) 100%
      );
      backdrop-filter: blur(10px);
      flex-shrink: 0;
      .input-container {
        flex: 1;
      }
      .input-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #78716c;
        font-weight: 500;
      }
      .send-btn {
        height: 60px;
        width: 60px;
        border-radius: 16px;
        background: linear-gradient(
          135deg,
          #fb923c 0%,
          #f59e0b 100%
        ) !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(251, 146, 60, 0.25);
        transition: all 0.3s ease;
      }
    }
  }
}
</style>
