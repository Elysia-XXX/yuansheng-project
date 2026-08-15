<script setup lang="ts">
</script>

<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <span class="app-title">原声分析平台</span>
      <nav class="app-nav">
        <router-link to="/">系统状态</router-link>
        <router-link to="/import">数据导入</router-link>
        <router-link to="/single">单条录入</router-link>
        <router-link to="/reviews">客户评价管理</router-link>
      </nav>
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
  justify-content: space-between;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.app-nav {
  display: flex;
  gap: 16px;
}

.app-nav a {
  color: #606266;
  text-decoration: none;
  font-size: 14px;
}

.app-nav a.router-link-exact-active {
  color: #409eff;
  font-weight: 600;
}
</style>
