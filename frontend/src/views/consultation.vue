<template>
  <div class="consultation-container">
    <div class="sidebar">
      <!-- AI助手信息 -->
      <div class="ai-assistant-info">
        <div class="breathing-circle">
          <el-image
            :src="iconUrl1"
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
          <div class="emotion-name">{{ currentEmotion.primaryEmotion }}</div>
          <div class="emotion-score">{{ currentEmotion.emotionScore }}</div>
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
            v-if="currentEmotion.improvementSuggestions?.length > 0"
          >
            <div class="actions-title">治愈小行动</div>
            <div class="actions-list">
              <div
                v-for="action in currentEmotion.improvementSuggestions"
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
            @click="handleSessionClick(session)"
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
                  @click="handleDeleteSession(session.id)"
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
              :src="iconUrl2"
              alt="用户头像"
              style="width: 30px; height: 30px"
            />
          </div>
          <div class="chat-info">
            <h2>宁渡AI助手</h2>
            <p>您的贴心AI心理健康助手</p>
          </div>
        </div>
        <el-button circle @click="creatNewFrontedSession" title="创建新会话">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <!-- 聊天消息区域 -->
      <div class="chat-messages">
        <!--欢迎用语 -->
        <div class="message-item ai-message" v-if="message.length === 0">
          <div class="message-avatar">
            <el-image
              :src="iconUrl1"
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
        <!-- 消息列表 -->
        <div
          v-for="msg in message"
          :key="msg.id"
          class="message-item"
          :class="msg.senderType === 2 ? 'ai-message' : 'user-message'"
        >
          <div class="message-avatar">
            <el-image
              v-if="msg.senderType === 2"
              :src="iconUrl1"
              style="width: 18px; height: 18px"
              alt="AI助手图标"
            />
            <el-image
              v-else
              :src="iconUrl3"
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
                v-html="formatMessageContent(msg.content)"
              ></p>
            </div>

            <div class="message-time">
              {{
                msg.senderType === 2 && isAityping
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
            v-model="userMessage"
            placeholder="请输入您想要分享的内容..."
            type="textarea"
            :rows="3"
            :disabled="isAityping"
            @keydown="handelKeydown"
            class="message-input"
            clearable
          ></el-input>
          <div class="input-footer">
            <span>按enter发送，按shift+enter换行</span>
            <span>{{ userMessage.length }}/500</span>
          </div>
        </div>
        <el-button
          :disabled="userMessage.length === 0 || userMessage.length > 500"
          class="send-btn"
          type="primary"
          @click="sendMessage"
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
import {
  startSession,
  getSessionList,
  deleteSession,
  getSessionDetail,
  getEmotionAnalysis,
} from "@/api/frontend";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import MarkdownRenderer from "@/components/MarkdownRenderer.vue";

const iconUrl1 = new URL("@/assets/images/1.png", import.meta.url).href;
const iconUrl2 = new URL("@/assets/images/2.png", import.meta.url).href;
const iconUrl3 = new URL("@/assets/images/13.png", import.meta.url).href;

// ---------- 情绪花园 ----------
const currentEmotion = ref({
  primaryEmotion: "中性",
  emotionScore: 50,
  isNegative: false,
  riskLevel: 1,
  suggestion: "情绪状态平稳",
  improvementSuggestions: [],
  riskDescription: "",
});

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
  const id = typeof sessionId === "number" ? sessionId.toString() : sessionId;
  try {
    const res = await getEmotionAnalysis(id);
    currentEmotion.value = res;
  } catch (err) {
    console.error("获取情绪分析失败:", err);
    ElMessage.error("获取情绪分析结果失败，请重试");
  }
};

// ---------- 会话管理 ----------
const currentSession = ref(null);
const sessionList = ref([]);
const message = ref([]); // 聊天消息数组
const userMessage = ref("");
const isAityping = ref(false);

// 创建临时前端会话
const creatNewFrontedSession = () => {
  // 清空聊天消息
  message.value = [];
  // 重置情绪花园
  currentEmotion.value = {
    primaryEmotion: "中性",
    emotionScore: 50,
    isNegative: false,
    riskLevel: 1,
    suggestion: "情绪状态平稳",
    improvementSuggestions: [],
    riskDescription: "",
  };
  // 创建临时会话
  const newSession = {
    sessionId: `temp-${Date.now()}`,
    status: "TEMP",
    sessionTitle: "新会话",
  };
  currentSession.value = newSession;
};

// 发送消息
const sendMessage = () => {
  if (!userMessage.value.trim()) return;
  if (isAityping.value) return;

  const userMsg = userMessage.value.trim();
  userMessage.value = "";

  // 添加用户消息
  message.value.push({
    id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    senderType: 1,
    content: userMsg,
    createdAt: new Date().toLocaleString(),
    isError: false,
  });

  if (currentSession.value?.status === "TEMP") {
    startNewSession(userMsg);
  } else {
    startAIResponse(currentSession.value.sessionId, userMsg);
  }
};

// 创建新会话并发送第一条消息
const startNewSession = async (userMsg) => {
  const SessionParams = {
    initialMessage: userMsg,
  };
  if (currentSession.value.sessionTitle === "新会话") {
    SessionParams.sessionTitle = `宁渡AI助手 - ${new Date().toLocaleString()}`;
  } else {
    SessionParams.sessionTitle = currentSession.value.sessionTitle;
  }

  try {
    const res = await startSession(SessionParams);
    // ✅ 使用后端返回的真实 sessionId，不加前缀
    const sessionData = {
      sessionId: res.sessionId,
      status: res.status,
      sessionTitle: SessionParams.sessionTitle,
    };
    if (currentSession.value.status === "TEMP") {
      Object.assign(currentSession.value, sessionData);
    } else {
      currentSession.value = sessionData;
    }
    getSessionPage();
    startAIResponse(currentSession.value.sessionId, userMsg);
  } catch (err) {
    console.error("创建会话失败:", err);
  }
};

// 流式对话
const startAIResponse = async (sessionId, userMessage) => {
  if (isAityping.value) {
    ElMessage.error("AI正在回复中，请稍后再试。");
    return;
  }
  isAityping.value = true;

  // 创建 AI 消息占位
  const aiMessage = {
    id: `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    senderType: 2,
    content: "",
    createdAt: new Date().toLocaleString(),
    isError: false,
  };
  message.value.push(aiMessage);

  const ctrl = new AbortController();
  fetchEventSource("/api/psychological-chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      sessionId,
      userMessageText: userMessage, // ← 改成 userMessageText
    }),
    signal: ctrl.signal,
    onopen: (response) => {
      const contentType = response.headers.get("Content-Type") || "";
      if (!contentType.includes("text/event-stream")) {
        ElMessage.error("服务器返回非流式数据");
        ctrl.abort();
        handleError("服务器返回非流式数据");
      }
    },
    onmessage: (event) => {
      const raw = event.data.trim();
      if (!raw) return;
      const eventName = event.event;
      const aiMessage = message.value[message.value.length - 1];
      if (eventName === "done") {
        isAityping.value = false;
        ctrl.abort();
        // 流结束后获取情绪分析
        getEmotionAnalysisData(currentSession.value.sessionId);
        return;
      }

      // ✅ 添加 try-catch 防止 JSON 解析崩溃
      try {
        const payload = JSON.parse(raw);
        const ok = String(payload.code) === "200";
        if (ok && payload.data?.content) {
          aiMessage.content += payload.data.content;
        } else {
          handleError(payload.message || "AI回复失败");
          ctrl.abort();
        }
      } catch (err) {
        handleError("数据解析失败");
        ctrl.abort();
      }
    },
    onerror: (err) => {
      handleError(err.message || "AI回复失败，请重试。");
      throw err;
    },
    onclose: () => {
      // 流结束后获取情绪分析
      getEmotionAnalysisData(currentSession.value.sessionId);
    },
  });
};

// 错误处理
const handleError = (error) => {
  const aiMessage = message.value[message.value.length - 1];
  if (aiMessage) {
    aiMessage.content = "AI回复失败，请重试";
    aiMessage.isError = true;
  }
  isAityping.value = false;
  ElMessage.error(error);
};

// 键盘事件
const handelKeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

// 获取会话列表
const getSessionPage = async () => {
  try {
    const res = await getSessionList({ pageNum: 1, pageSize: 10 });
    sessionList.value = res.records;
  } catch (err) {
    console.error("获取会话列表失败:", err);
  }
};

// 点击历史会话
const handleSessionClick = async (session) => {
  try {
    const res = await getSessionDetail(session.id);
    message.value = res;
    // ✅ 更新当前会话对象（使用后端真实 ID，不加前缀）
    const sessionData = {
      sessionId: session.id, // 直接使用原始 ID
      status: "ACTIVE",
      sessionTitle: session.sessionTitle,
    };
    currentSession.value = sessionData;
    // 获取该会话的情绪分析
    getEmotionAnalysisData(session.id);
  } catch (err) {
    console.error("获取会话详情失败:", err);
  }
};

// 删除会话
const handleDeleteSession = async (sessionId) => {
  try {
    await deleteSession(sessionId);
    ElMessage.success("删除成功");
    getSessionPage();
  } catch (err) {
    console.error("删除会话失败:", err);
    ElMessage.error("删除失败");
  }
};

// 换行处理
const formatMessageContent = (content) => {
  return content.replace(/\n/g, "<br>");
};

onMounted(() => {
  getSessionPage();
  creatNewFrontedSession();
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
      background: var(--card-bg); /* 原来复杂的半透明渐变，暗色下用纯色背景 */
      border-radius: 16px;
      padding: 16px;
      box-shadow: var(--card-shadow);
      border: 1px solid var(--border-color);
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
        color: var(--success-color); /* 保留绿色 */
        font-size: 12px;
        font-weight: 600;
        .status-dot {
          width: 8px;
          height: 8px;
          background: var(--success-color);
          border-radius: 50%;
          margin-right: 8px;
          animation: pulse 2s infinite;
          box-shadow: 0 0 8px rgba(5, 150, 105, 0.4);
        }
      }
    }
    .session-history {
      background: var(--session-item-bg);
      border-radius: 16px;
      padding: 16px;
      box-shadow: var(--card-shadow);
      margin-bottom: 20px;
      min-height: 250px;
      display: flex;
      flex-direction: column;
      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-color);
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
          background: var(--session-item-bg);
          &:hover {
            background: var(--session-item-hover);
            border-color: var(--active-border);
          }
          &.active {
            background: var(--session-item-active);
            border-color: var(--active-border);
          }
          .session-info {
            flex: 1;
            .session-title {
              font-weight: 500;
              font-size: 14px;
              color: var(--text-color);
              margin-bottom: 4px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
            .session-meta {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 6px;
              .session-time {
                font-size: 12px;
                color: var(--text-secondary);
              }
            }
            .session-preview {
              width: 200px;
              font-size: 12px;
              color: var(--text-secondary);
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
                color: var(--text-secondary);
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
        .no-sessions-text {
          text-align: center;
          font-size: 14px;
          color: var(--text-secondary);
        }
      }
    }
    .emotion-garden {
      background: var(--emotion-garden-bg);
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
          color: var(--text-color); /* 原来 #8b4513，暗色下保持可见 */
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
            color: var(--text-secondary);
            margin-right: 8px;
          }
          .status-emotion {
            font-size: 16px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 16px;
            display: inline-block;
            /* 保留原有颜色，或使用特殊变量，这里不改动 */
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
              background: var(--border-color);
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
            color: var(--text-secondary);
            font-weight: 500;
          }
        }
        .warm-suggestion {
          background: var(--card-bg);
          border-radius: 16px;
          padding: 12px;
          margin-bottom: 16px;
          display: flex;
          align-items: flex-start;
          gap: 10px;
          border: 1px solid var(--border-color);
          box-shadow: var(--card-shadow);
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
              color: var(--text-color);
              margin-bottom: 6px;
            }
            .suggestion-text {
              font-size: 13px;
              color: var(--text-secondary);
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
            color: var(--text-color);
            margin-bottom: 16px;
          }
          .actions-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            .action-item {
              background: var(--card-bg);
              border-radius: 12px;
              padding: 12px;
              display: flex;
              align-items: center;
              gap: 10px;
              border: 1px solid var(--border-color);
              box-shadow: var(--card-shadow);
              text-align: left;
              .action-icon {
                font-size: 14px;
                color: #ffd700;
                flex-shrink: 0;
              }
              .action-text {
                font-size: 12px;
                color: var(--text-secondary);
                line-height: 1.4;
                flex: 1;
              }
            }
          }
        }
        .risk-notice {
          background: var(--card-bg);
          border-radius: 16px;
          padding: 16px;
          display: flex;
          align-items: flex-start;
          gap: 12px;
          border: 1px solid var(--border-color);
          box-shadow: var(--card-shadow);
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
              color: var(--text-color);
              margin-bottom: 6px;
            }
            .notice-text {
              font-size: 13px;
              color: var(--text-secondary);
              line-height: 1.5;
            }
          }
        }
      }
    }
  }
  .chat-main {
    background: var(--card-bg);
    border-radius: 20px;
    box-shadow: var(--card-shadow);
    border: 1px solid var(--border-color);
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
      background: var(--card-bg);
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
        &.ai-message .message-avatar {
          background: linear-gradient(135deg, #fb923c, #f59e0b);
          box-shadow: 0 4px 12px rgba(251, 146, 60, 0.3);
        }
        &.user-message .message-avatar {
          background: linear-gradient(135deg, #6b7280, #4b5563);
          box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
        }
        .message-content {
          max-width: 70%;
          .message-bubble {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 12px 16px;
            position: relative;
            animation: fadeInUp 0.4s ease-out;
            border: 1px solid var(--border-color);
            box-shadow: var(--card-shadow);
            .typing-indicator {
              display: flex;
              gap: 4px;
              padding: 8px 0;
              .typing-dot {
                width: 8px;
                height: 8px;
                background: var(--text-secondary);
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
            color: var(--text-secondary);
            margin-top: 4px;
          }
        }
      }
    }
    .chat-input {
      border-top: 1px solid var(--border-color);
      padding: 20px 24px;
      display: flex;
      gap: 12px;
      align-items: flex-end;
      background: var(--card-bg);
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
        color: var(--text-secondary);
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
