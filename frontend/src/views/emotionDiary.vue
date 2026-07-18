<template>
  <div class="emotionDiary-container">
    <div class="header-section">
      <div class="header-content">
        <el-image
          :src="iconUrl"
          style="width: 60px; height: 60px"
          alt="Emotion Diary"
        />
        <h1>情绪日记</h1>
      </div>
    </div>
    <div class="content">
      <!-- 情绪评分 -->
      <div class="diary-card">
        <div class="title">今日情绪评分</div>
        <div class="section">
          <p>今天的整体情绪状态如何？(1-10分)</p>
          <div class="rate">
            <el-rate
              v-model="diaryForm.moodScore"
              :text="emotionStatus"
              :max="10"
              show-texts
              size="small"
            ></el-rate>
          </div>
        </div>
      </div>
      <!-- 主要情绪 -->
      <div class="diary-card">
        <div class="title">主要情绪</div>
        <div class="emotion-grid">
          <div
            v-for="emotion in emotionOptions"
            :key="emotion.name"
            class="emotion-card"
            @click="selectEmotion(emotion)"
            :class="{ selected: emotion.name === diaryForm.dominantEmotion }"
          >
            <el-image
              :src="emotion.url"
              style="width: 50px; height: 50px"
              alt="Emotion"
            />
            <div class="emotion-name">{{ emotion.name }}</div>
          </div>
        </div>
      </div>
      <!-- 详细记录 -->
      <div class="diary-card">
        <div class="title">详细记录</div>
        <div class="detail-form">
          <div class="form-group">
            <div class="form-label">情绪触发因素</div>
            <el-input
              v-model="diaryForm.emotionTriggers"
              placeholder="今天什么事情影响了您的情绪？"
              type="textarea"
              :rows="3"
              maxlength="1000"
              show-word-limit
            />
          </div>
          <div class="form-group">
            <div class="form-label">今日感想</div>
            <el-input
              v-model="diaryForm.diaryContent"
              placeholder="写下您今天的想法、感受或发生的有趣的事..."
              type="textarea"
              :rows="5"
              maxlength="2000"
              show-word-limit
            />
          </div>
          <!-- 生活指标 -->
          <div class="life-indicators">
            <div class="indicator-group">
              <div class="form-label">睡眠质量</div>
              <el-select v-model="diaryForm.sleepQuality" placeholder="请选择">
                <el-option label="很差" value="1"></el-option>
                <el-option label="较差" value="2"></el-option>
                <el-option label="一般" value="3"></el-option>
                <el-option label="良好" value="4"></el-option>
                <el-option label="优秀" value="5"></el-option>
              </el-select>
            </div>
            <div class="indicator-group">
              <div class="form-label">压力等级</div>
              <el-select v-model="diaryForm.stressLevel" placeholder="请选择">
                <el-option label="很低" value="1"></el-option>
                <el-option label="较低" value="2"></el-option>
                <el-option label="中等" value="3"></el-option>
                <el-option label="较高" value="4"></el-option>
                <el-option label="很高" value="5"></el-option>
              </el-select>
            </div>
          </div>
          <div class="action-buttons">
            <el-button @click="resetForm">重置</el-button>
            <el-button type="primary" @click="submitForm">提交</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive } from "vue";
import { dayjs, ElMessage } from "element-plus";
import { createEmotionalDiary } from "@/api/frontend";

const iconUrl = new URL("@/assets/images/2.png", import.meta.url).href;
//情绪评分
const emotionStatus = [
  "绝望崩溃",
  "消沉抑郁",
  "焦虑烦躁",
  "低落不悦",
  "平静淡然",
  "轻松惬意",
  "愉悦舒心",
  "欢欣满足",
  "兴奋欣喜",
  "极致幸福",
];
//情绪选项
const emotionOptions = [
  {
    name: "开心",
    url: new URL("@/assets/images/15.png", import.meta.url).href,
  },
  { name: "平静", url: new URL("@/assets/images/9.png", import.meta.url).href },
  {
    name: "焦虑",
    url: new URL("@/assets/images/14.png", import.meta.url).href,
  },
  { name: "悲伤", url: new URL("@/assets/images/5.png", import.meta.url).href },
  { name: "兴奋", url: new URL("@/assets/images/7.png", import.meta.url).href },
  { name: "疲惫", url: new URL("@/assets/images/3.png", import.meta.url).href },
  { name: "惊讶", url: new URL("@/assets/images/4.png", import.meta.url).href },
  { name: "困惑", url: new URL("@/assets/images/8.png", import.meta.url).href },
];

const diaryForm = reactive({
  diaryDate: dayjs().format("YYYY-MM-DD"),
  moodScore: 0,
  dominantEmotion: "",
  emotionTriggers: [],
  diaryContent: "",
  sleepQuality: null,
  stressLevel: null,
});

//选择情绪
const selectEmotion = (emotion) => {
  diaryForm.dominantEmotion = emotion.name;
};

//重置表单
const resetForm = () => {
  diaryForm.moodScore = 0;
  diaryForm.dominantEmotion = "";
  diaryForm.emotionTriggers = [];
  diaryForm.diaryContent = "";
  diaryForm.sleepQuality = null;
  diaryForm.stressLevel = null;
};

//提交表单
const submitForm = async () => {
  if (!diaryForm.moodScore) {
    ElMessage.error("请选择情绪评分");
    return;
  }
  try {
    await createEmotionalDiary(diaryForm);
    ElMessage.success("提交成功");
    resetForm();
  } catch (error) {
    ElMessage.error("提交失败");
  }
};
</script>
<style lang="scss" scoped>
.emotionDiary-container {
  background: var(--knowledge-bg-gradient); /* 或定义新变量，这里复用 */
  .header-section {
    background: linear-gradient(135deg, #7ed321 0%, #f5a623 100%);
    color: white;
    padding: 48px;
    .header-content {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  .content {
    margin: 0 auto;
    width: 980px;
    padding: 20px;
    .diary-card {
      margin-bottom: 20px;
      background: var(--card-bg);
      border-radius: 10px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      .title {
        margin-bottom: 20px;
        font-size: 25px;
        font-weight: 600;
        color: var(--text-color);
      }
      .section {
        margin-bottom: 20px;
        p {
          font-size: 15px;
          color: var(--text-secondary);
          margin-bottom: 15px;
        }
      }
      .emotion-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        .emotion-card {
          padding: 15px;
          border: 2px solid var(--emotion-card-border);
          border-radius: 15px;
          text-align: center;
          cursor: pointer;
          background: var(--emotion-card-bg);
          .emotion-name {
            margin-top: 10px;
            padding: 0 75px;
            color: var(--text-color);
          }
          &.selected {
            border-color: var(--emotion-card-selected-border);
            background: var(--emotion-card-selected-bg);
            transform: translateY(-3px);
          }
        }
      }
      .detail-form {
        .form-label {
          margin: 10px 0;
          color: var(--text-color);
        }
        .life-indicators {
          display: flex;
          gap: 20px;
          .indicator-group {
            flex: 1;
          }
        }
        .action-buttons {
          margin-top: 40px;
        }
      }
    }
  }
}
</style>
