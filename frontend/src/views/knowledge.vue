<template>
  <div>
    <PageHeader title="知识文章">
      <template #buttons>
        <el-button type="primary" @click="handelEdit({})">新增</el-button>
      </template>
    </PageHeader>
    <TableSearch :formItem="formItem" @search="handleSearch"></TableSearch>

    <el-table :data="tableData" style="width: 100%; margin-top: 25px">
      <el-table-column label="文章标题" fixed="left" width="200px">
        <template #default="scope">
          <div style="display: flex; align-items: center">
            <!--讲讲#default="scope" -->
            <el-icon><Timer /></el-icon>
            <span> {{ scope.row.title }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="分类" width="200px">
        <template #default="scope">
          <div style="display: flex; align-items: center">
            <el-icon><Timer /></el-icon>
            <span> {{ categoryMap[scope.row.category_id] }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="author_name" label="作者" width="150px" />
      <!-- 这里prop为啥直接就能获取到数据，因为最外层写了tableData？？？ -->
      <el-table-column prop="read_count" label="阅读量" width="130px" />
      <el-table-column prop="created_at" label="发布时间" width="180px">
        <template #default="scope">
          {{ dayjs(scope.row.created_at).format("YYYY-MM-DD HH:mm:ss") }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240px" fixed="right">
        <template #default="scope">
          <el-button @click="handelEdit(scope.row)" text type="primary"
            >编辑</el-button
          >
          <el-button
            @click="handelPublish(scope.row)"
            v-if="scope.row.status === 0 || scope.row.status === 2"
            type="success"
            text
            >发布</el-button
          >
          <el-button
            @click="handelUnpublish(scope.row)"
            v-if="scope.row.status === 1"
            type="warning"
            text
            >下线</el-button
          >
          <el-button @click="handelDelete(scope.row)" type="danger" text
            >删除</el-button
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
    <!--:page-size名字是固定的吗 -->
    <ArticleDialog
      v-model="dialogVisible"
      :categories="categories"
      :article="currentArticle"
      @success="handelSuccess"
    ></ArticleDialog>
  </div>
</template>
<script setup>
import { onMounted, ref, reactive } from "vue";
import PageHeader from "@/components/PageHeader.vue";
import TableSearch from "@/components/TableSearch.vue";
import {
  categoryTree,
  articlePage,
  getArticle,
  changeArticleStatus,
  deleteArticle,
} from "@/api/admin";
import ArticleDialog from "@/components/ArticleDialog.vue";
import { ElMessageBox, ElMessage } from "element-plus";
import dayjs from "dayjs";

const formItem = [
  {
    comp: "input",
    label: "搜索",
    prop: "title",
    placeholder: "请输入搜索内容",
  },
  {
    comp: "select",
    label: "分类",
    prop: "categoryId",
    placeholder: "请选择分类",
  },
  {
    comp: "select",
    label: "状态",
    prop: "status",
    placeholder: "请选择状态",
    options: [
      {
        label: "草稿",
        value: "0",
      },
      {
        label: "已发布",
        value: "1",
      },
      {
        label: "已下线",
        value: "2",
      },
    ],
  },
];
//分页参数
const pagination = reactive({
  currentPage: 1,
  size: 10,
  total: 0,
});

//分类映射
const categoryMap = reactive({});
//分类列表
const categories = ref([]);
//列表数据
const tableData = ref([]); //这里为什么用ref????
//查询知识文章列表
const handleSearch = async (formData) => {
  const params = {
    ...formData,
    ...pagination,
  };
  //知识文章列表
  const { records, total } = await articlePage(params); //articlePage是干什么的？？？
  tableData.value = records;
  pagination.total = total;
};

const handleChange = (page) => {
  pagination.currentPage = page;
  handleSearch();
};
handleSearch();
//文章新增和编辑
const dialogVisible = ref(false);
const currentArticle = ref(null);
const handelSuccess = () => {
  dialogVisible.value = false;
  handleSearch();
};
const handelEdit = (row) => {
  if (!row.id) {
    currentArticle.value = null;
    dialogVisible.value = true;
    return;
  }
  getArticle(row.id).then((res) => {
    currentArticle.value = res;
    dialogVisible.value = true;
  });
};

//发布
const handelPublish = (row) => {
  ElMessageBox.confirm(`确认发布文章${row.title}吗？`, `确认`, {
    confirmButtonText: "确认发布",
    cancelText: "取消",
    type: "info",
  }).then(() => {
    changeArticleStatus(row.id, 1).then((res) => {
      ElMessage.success("发布成功");
      handleSearch();
    });
  });
};

//下线
const handelUnpublish = (row) => {
  ElMessageBox.confirm(`确认下线文章${row.title}吗？`, `确认`, {
    confirmButtonText: "确认下线",
    cancelText: "取消",
    type: "warning",
  }).then(() => {
    changeArticleStatus(row.id, 2).then((res) => {
      ElMessage.success("下线成功");
      handleSearch();
    });
  });
};

//删除
const handelDelete = (row) => {
  ElMessageBox.confirm(`确认删除文章${row.title}吗？`, `确认`, {
    confirmButtonText: "确认删除",
    cancelText: "取消",
    type: "danger",
  }).then(() => {
    deleteArticle(row.id).then((res) => {
      ElMessage.success("删除成功");
      handleSearch();
    });
  });
};

onMounted(async () => {
  const res = await categoryTree();
  categories.value = res.map((item) => {
    categoryMap[item.value] = item.label;
    return {
      label: item.label,
      value: item.value,
    };
  });
  formItem[1].options = categories.value;
});
</script>
