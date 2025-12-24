<template>
  <el-container>
    <el-header>
      <div class="header-content">
        <h1>多模型协作翻译系统</h1>
        <el-menu
          mode="horizontal"
          :default-active="activeIndex"
          router
          class="header-menu"
        >
          <el-menu-item index="/">翻译</el-menu-item>
          <el-menu-item index="/history">历史记录</el-menu-item>
          <el-menu-item index="/glossary">术语表</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  min-height: 100vh;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.header-content h1 {
  font-size: 20px;
  margin: 0;
}

.header-menu {
  background-color: transparent;
  border: none;
}

.header-menu .el-menu-item {
  color: white !important;
}

.header-menu .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.15);
  color: white !important;
  border-radius: 4px;
  transition: all 0.3s;
}

.header-menu .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.25);
  color: white !important;
  border-radius: 4px;
  font-weight: 500;
}

/* 确保菜单文字在所有状态下都是白色 */
.header-menu .el-menu-item span {
  color: white !important;
}

.header-menu .el-menu-item:hover span {
  color: white !important;
}

.header-menu .el-menu-item.is-active span {
  color: white !important;
}

.el-main {
  padding: 20px;
  height: calc(100vh - 60px);
  overflow: hidden;
}
</style>

