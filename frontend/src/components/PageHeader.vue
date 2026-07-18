<template>
  <div class="page-header">
    <p class="page-title">{{ title }}</p>
    <div class="action-btn">
  <slot name="buttons"></slot>
</div>
  </div>
</template>
<script setup>
const props = defineProps({
  title: {
    type: String,
    default: '页面标题'
  }
})
</script>
<style lang="scss" scoped>
.page-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  .page-title {
    font-size: 20px;
    color: var(--page-header-title);
  }
}
</style>