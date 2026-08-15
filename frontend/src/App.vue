<script setup lang="ts">
</script>

<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <span class="app-title">原声分析平台</span>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
</style>
