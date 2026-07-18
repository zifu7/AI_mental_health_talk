<template>
  <div class="navbar">
    <div class="flex-box">
      <el-button @click="handleCollapse">
        <el-icon><Expand /></el-icon>
      </el-button>
      <p class="page-title">{{route.meta.title}}</p>
    </div>
    <div class="flex-box">
      <el-switch
    v-model="isDark"
    active-text="暗色"
    inactive-text="亮色"
    @change="toggleTheme"
    style="margin-right: 10px;"
  />
      <el-dropdown @command="handleCommand">
        <div class="flex-box">
          <el-avatar src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" size="medium" />
          <span class="user-name">admin</span>
          <el-icon class="el-icon--right">
            <arrow-down />
          </el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ArrowDown } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import {useRouter,useRoute} from 'vue-router'
import {ElMessageBox,ElMessage} from 'element-plus'
import { logout } from '@/api/admin'
import { ref, onMounted } from 'vue'

const isDark = ref(false)

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')           // 给 Element Plus 用
    document.documentElement.setAttribute('data-theme', 'dark') // 给你的自定义变量用
  } else {
    document.documentElement.classList.remove('dark')
    document.documentElement.removeAttribute('data-theme')
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
const router = useRouter()
const route = useRoute()

const handleCollapse = () => {
  useAdminStore().toggleCollapse()
}
const handleCommand = (command) => {
  if (command === 'logout') {
    // 退出登录逻辑
    ElMessageBox.confirm('确认退出登录吗？', '确认', {
      confirmButtonText: '确认退出',
      cancelText: '取消',
      type: 'warning'
    }).then(() => {
      logout().then(res => {
        //清除数据
        localStorage.removeItem("token")
          localStorage.removeItem("userInfo")
        ElMessage.success("退出登录成功")
        router.push("/auth/login")
      })
    })
 
  }
}

</script>

<style scoped lang="scss">
.navbar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  background-color: var(--navbar-bg);
  box-shadow: var(--card-shadow);
  border-bottom: 1px solid var(--navbar-border);

  .flex-box {
    display: flex;
    align-items: center;
    justify-content: center;

    .page-title {
      margin-left: 20px;
      font-size: 26px;
      font-weight: bold;
     color: var(--navbar-text);

    }

    .user-name {
      margin: 0 5px;
      font-weight: bold;
      color: var(--navbar-text);
    }
  }
}
</style>