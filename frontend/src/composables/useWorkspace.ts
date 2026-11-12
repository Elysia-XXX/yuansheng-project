import { computed, ref } from 'vue'
import type { AgentReply } from '../api/agent'

export type Message = { id: string; role: 'user' | 'assistant'; content: string; reply?: AgentReply }
export type Session = { id: string; title: string; messages: Message[] }
const key = 'yuansheng-agent-sessions-v1'
const fresh = (): Session => ({ id: crypto.randomUUID(), title: '新对话', messages: [] })
const sessions = ref<Session[]>([fresh()])
const collapsed = ref(false)
try {
  const saved = JSON.parse(localStorage.getItem(key) || 'null')
  if (Array.isArray(saved) && saved.length && saved.every(s => typeof s.id === 'string' && typeof s.title === 'string' && Array.isArray(s.messages) && s.messages.every((m: Message) => ['user', 'assistant'].includes(m.role) && typeof m.content === 'string'))) sessions.value = saved.slice(0, 10)
  collapsed.value = localStorage.getItem('yuansheng-sidebar-collapsed') === 'true'
} catch { /* Storage is optional. */ }
const activeId = ref(sessions.value[0]!.id)
const current = computed(() => sessions.value.find(s => s.id === activeId.value)!)
const busy = ref(false)
const storageError = ref('')
const mobileOpen = ref(false)
function save() {
  try { localStorage.setItem(key, JSON.stringify(sessions.value)); storageError.value = '' }
  catch { storageError.value = '浏览器存储不可用，本次对话仅保留在当前页面。' }
}
function newChat() {
  if (busy.value) return
  const session = fresh()
  sessions.value.unshift(session)
  sessions.value = sessions.value.slice(0, 10)
  activeId.value = session.id
  mobileOpen.value = false
  save()
}
function switchChat(session: Session) {
  if (busy.value) return
  activeId.value = session.id
  mobileOpen.value = false
}
function clearChats() {
  if (busy.value) return
  sessions.value = [fresh()]
  activeId.value = sessions.value[0]!.id
  save()
}
function toggleSidebar() {
  if (window.matchMedia('(max-width: 760px)').matches) mobileOpen.value = !mobileOpen.value
  else {
    collapsed.value = !collapsed.value
    try { localStorage.setItem('yuansheng-sidebar-collapsed', String(collapsed.value)) } catch { /* Optional preference. */ }
  }
}
export function useWorkspace() {
  return { sessions, activeId, current, busy, storageError, collapsed, mobileOpen, save, newChat, switchChat, clearChats, toggleSidebar }
}
