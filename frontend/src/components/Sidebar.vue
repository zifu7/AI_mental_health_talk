<template>
  <!-- :collapse="isCollapse"属性，用于控制侧边栏是否折叠 -->
  <el-aside width="isCollapse ? '64px' : '264px'">
    <el-menu
      :collapse="isCollapse"
      :collapse-transition="false"
      default-active="2"
      class="menu-style"
    >
      <div class="brand">
        <el-image
          style="width: 50px; height: 50px; margin-right: 10px"
          :src="iconURL"
          alt="logo"
        />
        <div class="info-card" v-show="!isCollapse">
          <h1 class="brand-title">心理健康AI助手</h1>
          <p class="brand-subtitle">管理后台</p>
        </div>
      </div>
      <el-menu-item
        @click="selectMenu"
        v-for="item in router.options.routes[0].children"
        :key="item.path"
        :index="item.path"
      >
        <el-icon><component :is="item.meta.icon" /></el-icon>
        <span>{{ item.meta.title }}</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup>
import { useAdminStore } from "@/stores/admin";
import { useRouter } from "vue-router";
import { computed } from "vue";
const router = useRouter();
const iconURL = new URL("@/assets/images/6.png", import.meta.url).href;
const selectMenu = (key) => {
  const currentRoute = router.options.routes[0];
  router.push(`${currentRoute.path}/${key.index}`);
};
const isCollapse = computed(() => useAdminStore().isCollapse);
</script>

<style scoped lang="scss">
.menu-style {
  height: 100%;
  .brand {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    background-color: var(--navbar-bg); /* 改为变量 */
    border-bottom: 1px solid var(--navbar-border);
    .info-card {
      .brand-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 5px;
        color: var(--navbar-text);
      }
      .brand-subtitle {
        font-size: 14px;
        color: var(--text-secondary);
      }
    }
  }
}
</style>
