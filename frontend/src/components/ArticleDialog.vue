<template>
  <!-- //子组件不能直接修改父组件传过来的props -->
  <el-dialog
    :title="isEdit ? '编辑文章' : '新增文章'"
    v-model="dialogVisible"
    width="50%"
    @close="handleClose"
  >
    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
      <!-- formData和formRef有啥区别？ -->
      <el-form-item label="标题" prop="title">
        <el-input
          v-model="formData.title"
          placeholder="请输入标题"
          maxlength="200"
          show-word-limit
        ></el-input>
      </el-form-item>
      <el-form-item label="所属分类" prop="categoryId">
        <!-- 这里写prop的作用 ？？？？-->
        <el-select v-model="formData.categoryId" placeholder="请选择分类">
          <el-option label="全部" value="" />
          <el-option
            v-for="opt in categories"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
          <!-- 这里的:value="opt.value"作用 -->
        </el-select>
      </el-form-item>
      <el-form-item label="文章摘要" prop="summary">
        <el-input
          type="textarea"
          v-model="formData.summary"
          placeholder="请输入摘要"
          maxlength="1000"
          show-word-limit
          rows="4"
        ></el-input>
      </el-form-item>
      <el-form-item label="标签" prop="tags">
        <el-select
          v-model="formData.tagArray"
          placeholder="请输入标签"
          multiple
          filterable
          allow-create
          width="100%"
        >
          <el-option
            v-for="tag in commonTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="封面图片">
        <div class="cover-upload">
          <el-upload
            class="avatar-uploader"
            action="#"
            :before-upload="beforeUpload"
            :http-request="handleUploadRequest"
            accept="image/*"
            :show-file-list="false"
          >
            <div v-if="!imgUrl" class="cover-placeholder">
              <p>点击上传图片</p>
            </div>
            <img v-else class="cover-image" :src="imgUrl" alt="封面图片" />
          </el-upload>
          <div v-if="imgUrl" class="cover-remove">
            <el-button type="danger" size="mini" @click="removeCover"
              >删除</el-button
            >
          </div>
        </div>
      </el-form-item>
      <el-form-item label="文章内容" prop="content">
        <RichTextEditor
          v-model="formData.content"
          placeholder="请输入文章内容,支持富文本格式"
          :maxCharCount="5000"
          @change="handleCountChange"
          @create="handleEditorCreated"
          min-height="400px"
        />
      </el-form-item>
    </el-form>
    <div v-if="btnreview">
      <h3>内容预览</h3>
      <div v-html="formData.content"></div>
    </div>
    <template #footer>
      <el-button @click="btnreview = !btnreview">{{
        btnreview ? "隐藏预览" : "预览效果"
      }}</el-button>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">{{
        isEdit ? "更新文章" : "新增文章"
      }}</el-button>
      <!-- 防止提交反复点击 -->
    </template>
  </el-dialog>
</template>
<script setup>
import { ref, computed, reactive, defineProps, nextTick, watch } from "vue";
import { ElMessage } from "element-plus";
import { uploadFile, createArticle, updateArticle } from "@/api/admin";
import { fileBaseUrl } from "@/config/index";
import RichTextEditor from "@/components/RichTextEditor.vue";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  categories: {
    type: Array,
    default: () => [],
  },
  article: {
    type: Object,
    default: null,
  },
});
const dialogVisible = computed({
  get: () => props.modelValue, //要读取数据时，返回props.modelValue的值
  set: (val) => emit("update:modelValue", val), //要设置数据时，调用emit方法，将val作为参数传递给父组件
});
const isEdit = computed(() => !!props.article?.id);

//监听编辑数据
const businessId = ref(""); //我有疑问，article是每次弹窗关闭都会清空吗？不然从有内容变为空也是变化
watch(
  () => props.article,
  (newVal) => {
    if (newVal) {
      Object.assign(formData, newVal);
      businessId.value = newVal.id;
      // 兼容 coverImage 和 cover_image 两种字段名
      const cover = newVal.coverImage || newVal.cover_image;
      imgUrl.value = cover ? fileBaseUrl + cover : "";
      formData.id = newVal.id;
    }
  },
);

const emit = defineEmits(["update:modelValue", "success"]);

const handleClose = () => {
  //重置表单
  formRef.value.resetFields();
  businessId.value = null;
  removeCover();
  formData.tagArray = [];
  emit("update:modelValue", false);
};
const formData = reactive({
  title: "",
  content: "",
  coverImage: "",
  categoryId: 1,
  summary: "",
  tags: "",
  id: "",
  tagArray: [],
});
const rules = reactive({
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
  categoryId: [{ required: true, message: "请选择分类", trigger: "change" }],
  content: [
    { required: true, message: "请输入文章内容", trigger: "blur" },
    { max: 5000, message: "文章内容长度必须小于5000个字符", trigger: "blur" },
  ],
});
const commonTags = [
  "情绪管理",
  "焦虑",
  "抑郁",
  "压力",
  "睡眠",
  "冥想",
  "正念",
  "放松",
  "心理健康",
  "自我成长",
  "人际关系",
  "工作压力",
  "学习方法",
  "生活技巧",
];
//上传
const imgUrl = ref("");
const beforeUpload = (file) => {
  const isImage = file.type.startsWith("image/");
  const isLt5M = file.size / 1024 / 1024 < 5;
  if (!isImage) {
    ElMessage.error("请上传图片");
    return false;
  }
  if (!isLt5M) {
    ElMessage.error("图片大小不能超过5MB");
    return false;
  }
  return true;
};
const handleUploadRequest = async ({ file }) => {
  //这里的file没写{}就报错了。。。。  http-request要写解构赋值，否则会报    错，因为file是一个对象，而不是一个文件
  businessId.value = crypto.randomUUID();
  const fileRes = await uploadFile(file, businessId.value);
  //地址拼接
  imgUrl.value = fileBaseUrl + fileRes.filePath;
  formData.coverImage = fileRes.filePath;
};
const removeCover = () => {
  imgUrl.value = "";
  formData.coverImage = "";
};
//富文本
const handleCountChange = (data) => {
  formData.content = data.html;
};

const editorInstance = ref(null);
const handleEditorCreated = (editor) => {
  editorInstance.value = editor;
  if (formData.content && editor) {
    nextTick(() => {
      editor.setHtml(formData.content);
    });
  }
};
const btnreview = ref(false);
const loading = ref(false);
const formRef = ref(null);
const handleSubmit = () => {
  //这里不用传formRef，为啥？
  formRef.value.validate((valid) => {
    if (valid) {
      loading.value = true;
      const submitData = {
        ...formData,
        tags: formData.tagArray.join(","), //tag原来是数组,现在要转换为字符串
      };
      delete submitData.tagArray;
      if (isEdit.value) {
        //更新
        updateArticle(submitData, props.article.id).then((res) => {
          //这里是不是能换一种写法，不用then??
          loading.value = false;

          emit("success");
        });
      } else {
        //创建

        createArticle(submitData).then((res) => {
          //createArticle的作用？是把收到的数据传给后端吗？
          loading.value = false;

          emit("success");
        });
      }
    } else {
      ElMessage.error("请填写完整信息");
    }
  });
};
</script>
<style lang="scss" scoped>
.cover-placeholder {
  width: 200px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--cover-placeholder-color);
  background: var(--cover-placeholder-bg);
}
.cover-image {
  width: 200px;
  height: 120px;
  display: block;
}
</style>
