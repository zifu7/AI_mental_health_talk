<template>
  <div class="container">
    <div class="title">
      <div class="back-home">
        <el-icon><Back /></el-icon>
        <span style="cursor: pointer" @click="router.push('/')">返回首页</span>
      </div>
      <div class="title-text">
        <h2>登录您的账户</h2>
        <p>请输入您的登录信息</p>
      </div>
    </div>
    <div class="form-contianer">
      <el-form
        ref="ruleFormRef"
        :model="formData"
        :rules="rules"
        label-position="top"
      >
        <el-form-item label="用户名或邮箱" prop="username">
          <el-input
            v-model="formData.username"
            size="large"
            placeholder="请输入用户名或邮箱"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            size="large"
            placeholder="请输入密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-button
          class="btn"
          type="primary"
          size="large"
          @click="submitForm(ruleFormRef)"
          >登录</el-button
        >
      </el-form>
      <div class="footer">
        <p>还没有账号？<router-link to="/auth/register">去注册</router-link></p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { login } from "@/api/admin";
const router = useRouter();
const formData = reactive({
  username: "",
  password: "",
});
const ruleFormRef = ref();
const rules = reactive({
  username: [
    { required: true, message: "请输入用户名或邮箱", trigger: "blur" },
  ],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
});
const submitForm = async (formEl) => {
  if (!formEl) return;
  try {
    // 1. 表单验证（不传回调，直接 await）
    const valid = await formEl.validate();
    if (!valid) return;
    // 2. 发起登录请求
    const data = await login(formData);
    // 3. 处理响应
    if (!data.token) {
      ElMessage.error("登录失败");
      return;
    }
    localStorage.setItem("token", data.token);
    localStorage.setItem("userInfo", JSON.stringify(data.userInfo));
    ElMessage.success("登录成功");
    if (data.userInfo.user_type === 2) {
      router.push("/back/dashboard");
    } else {
      router.push("/");
    }
  } catch (error) {
    console.error("登录过程出错", error);
    // 响应拦截器已处理大部分错误提示，这里兜底
    const msg = typeof error === "string" ? error : error?.message;
    if (msg) {
      ElMessage.error(msg);
    }
  }
};
</script>
<style lang="scss" scoped>
.container {
  width: 384px;
  .title {
    .back-home {
      margin-bottom: 60px;
    }
    .title-text {
      text-align: center;
      h2 {
        font-size: 36px;
        margin-bottom: 10px;
      }
      p {
        font-size: 18px;
        color: #6b7280;
      }
    }
  }
  .form-contianer {
    margin-top: 30px;
    .btn {
      margin-top: 40px;
      width: 100%;
    }
    .footer {
      padding: 30px;
      text-align: center;
    }
  }
}
</style>
