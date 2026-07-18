<template>
  <div class="knowledge-container">
    <div class="header-section">
      <div class="header-content">
        <el-image
          :src="iconUrl"
          style="width: 60px; height: 60px"
          alt="心理健康知识库"
        />
        <h1>心理健康知识库</h1>
      </div>
    </div>
    <div class="content">
      <!-- 左侧菜单 -->
      <div class="recommend-section">
        <div class="section-title">推荐阅读</div>
        <div class="recommend-list">
          <div
            v-for="item in recommendList"
            :key="item.id"
            class="recommend-item"
            @click="gotoArticle(item.id)"
          >
            <h4>{{ item.title }}</h4>
            <p class="read-count">
              <el-icon><Histogram /></el-icon>
              阅读量：{{ item.read_count }}
            </p>
          </div>
        </div>
      </div>
      <!-- 右侧内容 -->
      <div class="article-list">
        <div
          v-for="item in articleList"
          :key="item.id"
          class="article-item"
          @click="gotoArticle(item.id)"
        >
          <el-image
            style="width: 240px; height: 150px"
            :src="getImage(item.cover_image)"
            alt="文章封面"
          />
          <div class="info">
            <div class="title">
              <h3>{{ item.title }}</h3>
              <el-tag Plain type="primary">{{ item.categoryName }}</el-tag>
            </div>
            <div :style="{ marginTop: '10px' }">
              <div class="flex-box">
                <el-icon><Avatar /></el-icon>
                <span>{{ item.authorName }}</span>
              </div>
              <div class="flex-box">
                <el-icon><List /></el-icon>
                <span>{{ dayjs(item.updatedAt).format("YYYY-MM-DD") }}</span>
              </div>
              <div :style="{ marginTop: '10px' }">
                <div class="flex-box">
                  <el-icon><Platform /></el-icon>
                  <span>观看人数：{{ item.readCount }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        style="margin-top: 25px"
        :page-size="pagination.size"
        small
        layout="prev, pager, next"
        :total="pagination.total"
        @change="handleChange"
      >
      </el-pagination>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from "vue";
import { getKnowledgeList } from "@/api/frontend";
import { dayjs } from "element-plus";
import { useRouter } from "vue-router";
import { fileBaseUrl } from "@/config/index";
const router = useRouter();

const iconUrl = new URL("@/assets/images/11.png", import.meta.url).href;
// 推荐列表
const recommendList = ref([]);
//右侧列表
const pagination = reactive({
  currentPage: 1,
  size: 10,
  total: 0,
});

const articleList = ref([]);
//获取列表数据
// 获取列表数据
const getPageList = () => {
  const params = {
    sortField: "publishedAt",
    sortDirection: "desc",
    ...pagination,
  };
  getKnowledgeList(params).then((res) => {
    // 字段映射：将下划线转为驼峰
    const records = (res.records || []).map((item) => ({
      ...item,
      categoryName: item.category_name,
      authorName: item.author_name,
      readCount: item.read_count,
      updatedAt: item.updated_at,
      createdAt: item.created_at,
      coverImage: item.cover_image, // 可选，因为 getImage 已兼容
      tagArray: item.tagArray || [],
    }));
    articleList.value = records;
    pagination.total = res.total;
  });
};

const getImage = (url) => {
  if (!url) return "https://file.itndedu.com/psychology_ai.png";
  const fullUrl = fileBaseUrl + url;
  return fullUrl;
};
const handleChange = (page) => {
  pagination.currentPage = page;
  getPageList();
};

// 跳转文章详情页
const gotoArticle = (id) => {
  router.push({ path: "/knowledge/article/" + id });
};

onMounted(() => {
  const params = {
    sortField: "read_count",
    sortDirection: "desc",
    currentPage: 1,
    size: 5,
  };
  getPageList();
  getKnowledgeList(params).then((res) => {
    recommendList.value = res.records;
  });
});
</script>
<style lang="scss" scoped>
.knowledge-container {
  background: var(--knowledge-bg-gradient);
  min-height: 100vh; /* 保证全页有底色 */

  .flex-box {
    display: flex;
    align-items: center;
    span {
      margin-left: 10px;
      color: var(--text-primary);
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
    display: flex;
    gap: 20px;
    margin: 0 auto;
    width: 1200px;
    padding: 20px;
    background: transparent; /* 让父级渐变色透出，或按需改为 var(--main-bg) */

    .recommend-section {
      width: 280px;
      background: var(--card-bg); /* 这里已有 */
      border-radius: 12px;
      box-shadow: var(--card-shadow);
      padding: 15px;
      height: 400px;

      .section-title {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 5px;
      }

      .recommend-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;

        .recommend-item {
          border-left: 4px solid #f59e0b;
          padding-left: 10px;
          cursor: pointer;
          color: var(--text-primary);

          .read-count {
            margin-top: 15px;
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 10px;
          }
        }
      }
    }

    .article-list {
      flex: 1;

      .article-item {
        background: var(--card-bg); /* 这里已有 */
        border-radius: 12px;
        box-shadow: var(--card-shadow);
        padding: 15px;
        margin-bottom: 20px;
        display: flex;
        color: var(--text-primary);

        .info {
          margin-left: 20px;

          .title {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-primary);

            h3,
            span,
            a {
              color: inherit;
            }
          }

          p {
            color: var(--text-secondary);
          }
        }
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    padding-bottom: 30px;
    background: transparent; /* 保持透明，让整体渐变可见 */
  }
}
</style>
