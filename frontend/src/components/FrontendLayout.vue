<template>
  <div class="frontend-layout">
    <div class="navbar-container">
      <div class="brand-section">
          <el-image :src="iconUrl" style="height: 50px;width: 50px;" alt="品牌logo" class="brand-logo"></el-image>
       <h1 class="brand-name">心理健康AI助手</h1>
      </div>
      <div class="nav-section">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/consultation" class="nav-link" v-if="isLoggedIn">AI咨询</router-link>
        <router-link to="/emotion-diary" class="nav-link" v-if="isLoggedIn">情绪日记</router-link>
        <router-link to="/knowledge" class="nav-link">知识库</router-link>
        <el-button type="primary" class="logout-btn" v-if="isLoggedIn" @click="handleLogout">退出登录</el-button>
        <template v-else>
          <router-link to="/auth/login" class="nav-link">登录</router-link>
          <router-link to="/auth/register" class="nav-link">
            <el-button type="primary">
              注册                                  <!--为什么不用button标签,非要使用el-button吗 -->
            </el-button>
          </router-link>
        </template>
        <el-switch
          v-model="isDark"
          active-text="暗色"
          inactive-text="亮色"
          @change="toggleTheme"
        />
      </div>
    </div>
    <div class="main-content">
      <router-view></router-view>
    </div>
    <div class="footer-container">
      <div class="footer-bottom">
        <p>
          &copy; 2026 心理健康AI助手. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
const router = useRouter()



const iconUrl = new URL('@/assets/images/6.png', import.meta.url).href

const isLoggedIn = ref(false)

const handleLogout = () => {
  localStorage.removeItem("token")
  isLoggedIn.value = false
  ElMessage.success("退出登录成功")
  router.push("/auth/login")
}

const isDark = ref(false)

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})

const toggleTheme = (val) => {
  if (val) {
    document.documentElement.classList.add('dark')
    document.documentElement.setAttribute('data-theme', 'dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    document.documentElement.removeAttribute('data-theme')
    localStorage.setItem('theme', 'light')
  }
}
onMounted(() => {
  isLoggedIn.value = localStorage.getItem("token") !== null
})
</script>
<style lang="scss" scoped>
.frontend-layout {
  background-color: var(--frontend-navbar-bg);
  .navbar-container {
    max-width: 1200px;
    height: 100%;
    margin: 0 auto;
    padding: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    .brand-section {
      display: flex;
      align-items: center;
      .brand-name {
        margin-left: 10px;
        font-size: 24px;
        font-weight: 600;
        color: var(--text-color);
      }
    }
    .nav-section {
      display: flex;
      align-items: center;
      gap: 40px;
      .nav-link {
        color: var(--frontend-navbar-text);
        font-size: 16px;
        font-weight: 500;
        &:hover {
          color: var(--frontend-navbar-hover);
        }
      }
    }
  }

  .footer-container {
    background: #1f2937; /* 页脚保持深色固定 */
    color: white;
    padding: 15px 0;
    margin-top: auto;
    .footer-bottom {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 10px;
      text-align: center;
    }
  }
}
</style>
