<template>
  <div class="backend-layout">
    <el-container class="main-container">
        <Sidebar></Sidebar>
      <el-container>
        <el-header>
          <Navbar></Navbar>
        </el-header>
        <el-main class="main-content" >
          <router-view class="content-contain" style="height: 900px;"></router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'
</script>

<style lang="scss" scoped>
.backend-layout {
  height: 100vh;
  .el-header {
    height: 74px !important;
  }
  .main-container {
    height: 100%;
  }
  .content-contain {
    height: calc(100% - 74px);
    background: var(--main-bg);       /* 改为变量 */
    padding: 20px;
  }
}
</style>