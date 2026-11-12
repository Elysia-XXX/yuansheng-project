<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { nextTick, onMounted, ref, watch } from 'vue'
import { agentStatus } from './api/agent'
import AppIcon from './components/AppIcon.vue'
import { useWorkspace, type Session } from './composables/useWorkspace'
const route = useRoute()
const router = useRouter()
const demo = ref(false)
const { sessions, activeId, busy, collapsed, mobileOpen, newChat, switchChat, toggleSidebar } = useWorkspace()
const sidebarEl = ref<HTMLElement>()
const mainEl = ref<HTMLElement>()
watch(mobileOpen, async (open) => {
  await nextTick()
  const target = open ? sidebarEl.value?.querySelector<HTMLButtonElement>('.sidebar-toggle') : mainEl.value?.querySelector<HTMLButtonElement>('.mobile-menu')
  target?.focus()
})
onMounted(async () => { try { demo.value = (await agentStatus()).mode === 'demo' } catch { /* The workspace shows connection guidance. */ } })
function createChat() { if (busy.value) return; newChat(); router.push('/') }
function openChat(session: Session) { if (busy.value) return; switchChat(session); router.push('/') }
</script>

<template>
  <div class="shell" :class="{ 'sidebar-collapsed': collapsed, 'mobile-nav-open': mobileOpen }" @keydown.esc="mobileOpen = false">
    <button v-if="mobileOpen" class="sidebar-backdrop" aria-label="关闭导航" @click="mobileOpen = false"></button>
    <aside ref="sidebarEl" class="navigation" aria-label="工作区导航">
      <div class="sidebar-brand-row"><router-link class="brand" to="/" aria-label="原声工作台首页"><AppIcon name="voice" :size="26" /><span>原声<span class="brand-subtitle">Agent</span></span></router-link><button class="icon-button sidebar-toggle" :aria-label="collapsed ? '展开侧栏' : '收起侧栏'" :aria-expanded="!collapsed" @click="toggleSidebar"><AppIcon name="panel" /></button></div>
      <button class="new-chat-button" :disabled="busy" title="新对话" @click="createChat"><AppIcon name="new" /><span>新对话</span><kbd>＋</kbd></button>
      <nav class="main-nav" aria-label="主导航" @click="mobileOpen = false">
        <router-link to="/" title="对话分析"><AppIcon name="chat" /><span>对话分析</span></router-link>
        <router-link to="/reviews" title="原声数据"><AppIcon name="data" /><span>原声数据</span></router-link>
        <router-link to="/import" title="导入数据"><AppIcon name="upload" /><span>导入数据</span></router-link>
        <router-link to="/single" title="录入原声"><AppIcon name="plus" /><span>录入原声</span></router-link>
        <a href="/legacy.html" target="_blank" rel="noopener" :aria-disabled="demo" :title="demo ? '经典看板需要真实数据库模式' : '打开经典看板'" @click="demo && $event.preventDefault()"><AppIcon name="chart" /><span>经典看板</span><AppIcon class="external-icon" name="external" :size="13" /></a>
      </nav>
      <section class="sidebar-history" aria-label="最近对话"><h2>最近对话</h2><button v-for="session in sessions" :key="session.id" :disabled="busy" :class="{ active: activeId === session.id && route.path === '/' }" :title="session.title" @click="openChat(session)"><span>{{ session.title }}</span></button></section>
      <footer class="nav-foot"><button class="icon-button collapsed-toggle" aria-label="展开侧栏" @click="toggleSidebar"><AppIcon name="panel" /></button><router-link to="/status" title="服务状态" @click="mobileOpen = false"><AppIcon name="settings" /><span>服务状态</span></router-link><div class="workspace-profile"><span class="profile-avatar">声</span><div>原声工作空间<small>{{ demo ? '本地演示' : '数据分析助手' }}</small></div></div></footer>
    </aside>
    <main ref="mainEl" class="main-area" :class="{ 'workspace-page': route.path === '/' }" :inert="mobileOpen">
      <button v-if="route.path !== '/'" class="icon-button mobile-menu" aria-label="打开导航" @click="toggleSidebar"><AppIcon name="menu" /></button>
      <div v-if="demo && route.path !== '/'" class="demo-data-guide"><h1>此功能需要连接业务数据库</h1><p>当前演示模式仅提供对话查询与计算。配置 PostgreSQL 并关闭演示模式后，可使用原声管理、数据导入和经典看板。</p><router-link to="/">返回对话工作台</router-link></div>
      <router-view v-else />
    </main>
  </div>
</template>
