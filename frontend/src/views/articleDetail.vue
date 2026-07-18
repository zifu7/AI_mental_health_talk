<template>
  <div class="articleDetail-container">
    <div class="header-section">
      <div class="header-content">
        <el-image
          :src="iconUrl"
          style="width: 60px; height: 60px"
          class="header-image"
        ></el-image>
        <h1>知识文章详细</h1>
      </div>
    </div>
    <div class="content">
      <div class="diary-card">
        <p class="title">文章信息</p>
        <div class="sub-title">
          <el-tag size="large" class="category-tag">{{
            articleDetail.categoryName
          }}</el-tag>
          <div class="flex-box">
            <el-icon><List /></el-icon>
            <span>{{
              dayjs(articleDetail.updatedAt).format("YYYY-MM-DD")
            }}</span>
          </div>
        </div>
        <h1 class="article-title">{{ articleDetail.title }}</h1>
        <div class="summary-content" v-if="articleDetail.summary">
          <p>{{ articleDetail.summary }}</p>
        </div>
        <div :style="{ marginTop: '20px' }" class="flex-box">
          <div class="item flex-box">
            <el-icon><Avatar /></el-icon>
            <span>{{ articleDetail.authorName }}</span>
          </div>
          <div class="item flex-box">
            <el-icon><Platform /></el-icon>
            <span>{{ articleDetail.readCount }}</span>
          </div>
        </div>
      </div>
      <div class="diary-card">
        <div class="title">正文内容</div>
        <div
          class="content-wrapper"
          v-html="formatContent(articleDetail.content)"
        ></div>
        <div
          class="tags-content"
          v-if="articleDetail.tagArray && articleDetail.tagArray.length"
        >
          <h4 class="tags-title">相关标签</h4>
          <div class="tags-list">
            <el-tag
              v-for="tag in articleDetail.tagArray"
              :key="tag"
              class="tag-item"
              type="info"
              effect="light"
              >{{ tag }}</el-tag
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { getKnowledgeDetail } from "@/api/frontend";
import { dayjs } from "element-plus";

const iconUrl = new URL("@/assets/images/11.png", import.meta.url).href;
const props = defineProps({
  id: {
    type: String,
  },
});
const articleDetail = ref({});

const formatContent = (content) => {
  if (!content) return "";

  // 基本的HTML清理和格式化
  let formatted = content
    .replace(/\n/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");

  return formatted;
};
onMounted(() => {
  getKnowledgeDetail(props.id).then((res) => {
    const mapped = {
      ...res,
      categoryName: res.category_name,
      authorName: res.author_name,
      readCount: res.read_count,
      coverImage: res.cover_image,
      updatedAt: res.updated_at,
      createdAt: res.created_at,
      tagArray: res.tagArray || [],
      summary: res.summary || "",
    };
    articleDetail.value = mapped;
  });
});
</script>
<style scoped lang="scss">
.articleDetail-container {
  background: var(--knowledge-bg-gradient);
  .flex-box {
    display: flex;
    align-items: center;
    .item {
      margin-right: 20px;
      span {
        margin-left: 5px;
        color: var(--text-color);
      }
    }
  }
  .header-section {
    background: linear-gradient(135deg, #f59e0b 0%, #8b5cf6 100%);
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
        margin-bottom: 15px;
        font-size: 20px;
        font-weight: 600;
        color: var(--text-color);
      }
      .sub-title {
        margin-top: 20px;
        display: flex;
        align-items: center;
        .category-tag {
          margin-right: 20px;
        }
      }
      .article-title {
        font-size: 28px;
        font-weight: bold;
        color: var(--text-color);
        margin-top: 30px;
        margin-bottom: 10px;
      }
      .summary-content {
        background: rgba(126, 211, 33, 0.1);
        border-left: 4px solid #7ed321;
        padding: 10px 15px;
        border-radius: 0 8px 8px 0;
        position: relative;
        color: var(--text-color);
      }
      .content-wrapper {
        font-size: 15px;
        color: var(--text-color);
        :deep(p) {
          margin-bottom: 10px;
        }
        :deep(h1),
        :deep(h2),
        :deep(h3),
        :deep(h4),
        :deep(h5),
        :deep(h6) {
          margin: 15px 0 10px;
          color: var(--text-color);
          font-weight: 600;
        }
        :deep(h2) {
          font-size: 15px;
          border-bottom: 2px solid var(--border-color);
          padding-bottom: 5px;
        }
        :deep(h3) {
          font-size: 13px;
        }
        :deep(ul),
        :deep(ol) {
          padding-left: 15px;
          margin-bottom: 10px;
        }
        :deep(li) {
          margin-bottom: 5px;
        }
      }
      .tags-content {
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
        .tags-title {
          margin-bottom: 10px;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-color);
        }
        .tags-list {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }
      }
    }
  }
}
</style>
