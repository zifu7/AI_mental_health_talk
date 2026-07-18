<template>
  <div>
    <PageHeader title="咨询记录"></PageHeader>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column label="会话ID" width="100">
        <template #default="scope">
          <el-avatar>{{ scope.row.userNickname }}</el-avatar>
        </template>
      </el-table-column>
      <el-table-column label="情绪日志">
        <template #default="scope">
          <div class="session-title">{{ scope.row.sessionTitle }}</div>
          <div class="session-preview">{{ scope.row.lastMessageContent }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="messageCount" label="消息数" width="100" />
      <el-table-column prop="lastMessageTime" label="时间" width="100" />
      <el-table-column label="操作" width="100">
        <template #default="scope">
          <el-button type="primary" text @click="viewSessionDetail(scope.row)"
            >详情</el-button
          >
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top: 25px"
      :page-size="pagination.size"
      small
      layout="prev, pager, next"
      :total="pagination.total"
      @change="handleChange"
    >
    </el-pagination>
    <el-dialog
      v-model="showDetailDialog"
      title="会话详情"
      width="70%"
      :close-on-click-modal="false"
      v-loading="messageLoading"
    >
      <div class="session-detail">
        <div class="detail-header">
          <div class="detail-row">
            <div class="detail-label">用户：</div>
            <div class="detail-value">{{ currentSession.userNickname }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">开始时间：</div>
            <div class="detail-value">{{ currentSession.startedAt }}</div>
          </div>
          <div class="detail-row">
            <div class="detail-label">消息数：</div>
            <div class="detail-value">{{ currentSession.messageCount }}</div>
          </div>
        </div>
        <div class="messages-container">
          <div class="messages-header">
            <h4>对话记录</h4>
          </div>
          <div class="messages-list">
            <div
              v-for="message in sessionMessages"
              :key="message.id"
              class="message-item"
              :class="message.senderType === 1 ? 'user-message' : 'ai-message'"
            >
              <div class="message-header">
                <span class="sender">{{
                  message.senderType === 1 ? "用户" : "AI助手"
                }}</span>
                <span class="time">{{ message.createdAt }}</span>
              </div>
              <div class="message-content">{{ message.content }}</div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import PageHeader from "@/components/PageHeader.vue";
import { onMounted, ref, reactive } from "vue";
import { getConsultations, getSessionDetail } from "@/api/admin";

const tableData = ref([]);
const pagination = reactive({
  currentPage: 1,
  size: 10,
  total: 0,
});
//当前会话详情信息
const currentSession = ref({});
const sessionMessages = ref([]);
const messageLoading = ref(false);
const viewSessionDetail = (row) => {
  messageLoading.value = true;

  getSessionDetail(row.id).then((res) => {
    messageLoading.value = false;
    sessionMessages.value = res;
    currentSession.value = row;
    showDetailDialog.value = true;
  });
};
const handelSearch = () => {
  getConsultations(pagination).then((res) => {
    //这是不是可以换一种写法？？？
    const { records, total } = res;
    pagination.total = total;
    tableData.value = records;
  });
};
const handleChange = (val) => {
  pagination.currentPage = val;
  handelSearch();
};
const showDetailDialog = ref(false);
onMounted(() => {
  handelSearch();
});
</script>
<style lang="scss" scoped>
.session-title {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
}
.session-preview {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.session-detail {
  max-height: 70vh;
  overflow-y: auto;
  .detail-header {
    margin-bottom: 20px;
    padding: 16px;
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }

  .detail-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    :last-child {
      margin-bottom: 0;
    }
    .detail-label {
      font-weight: 500;
      color: var(--text-color);
      min-width: 80px;
      margin-right: 8px;
    }

    .detail-value {
      color: var(--text-color);
    }
  }
}
.messages-container {
  margin-top: 20px;
  .messages-header {
    margin-bottom: 16px;
    h4 {
      margin: 0;
      color: var(--text-color);
      font-size: 16px;
      font-weight: 500;
    }
  }
  .messages-list {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    background: var(--card-bg);
    .message-item {
      margin-bottom: 12px;
      padding: 12px;
      border-radius: 8px;
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      :last-child {
        margin-bottom: 0;
      }
      &.user-message {
        background: var(--message-user-bg);
      }

      &.ai-message {
        background: var(--message-ai-bg);
      }
    }
    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      .sender {
        font-weight: 500;
        color: var(--text-color);
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .time {
        font-size: 12px;
        color: var(--text-secondary);
      }

      .message-content {
        color: var(--text-color);
        line-height: 1.6;
        white-space: pre-wrap;
        margin-top: 8px;
        font-size: 14px;
      }
    }
  }
}
</style>
