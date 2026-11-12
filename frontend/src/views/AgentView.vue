<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { agentStatus, sendChat, type AgentStatus, type ToolCall } from '../api/agent'
import AppIcon from '../components/AppIcon.vue'
import { useWorkspace } from '../composables/useWorkspace'

const { activeId, current, busy, storageError, save, clearChats, toggleSidebar } = useWorkspace()
const panelOpen = ref(false)
const status = ref<AgentStatus>()
const statusError = ref('')
const error = ref('')
const input = ref('')
const selected = ref<ToolCall>()
const pane = ref<'result' | 'trace'>('result')
const showTools = ref(false)
const log = ref<HTMLElement>()
const suggestions = ['按品类统计客户原声，并查看典型反馈', '查看京东的差评及原文', '搜索包含“噪音”的原声', '计算 (128 - 96) / 96 * 100']
const toolNames: Record<string, string> = { describe_data: '查看数据说明', search_records: '查找客户原声', aggregate_records: '统计数据分布', get_record: '查看原声详情', calculate: '执行计算' }
const calls = computed(() => current.value.messages.flatMap(m => m.reply?.tool_calls || []))
const groups = computed(() => (selected.value?.result.groups || []) as { label: string; count: number; share_percent: number }[])
const records = computed(() => (selected.value?.result.items || []) as { id: number; text: string; platform: string; category_l3: string }[])
const maxCount = computed(() => Math.max(...groups.value.map(g => g.count), 1))
const citations = (text: string) => [...new Set([...text.matchAll(/\[原声\s*#(\d+)\]/g)].map(m => m[1]!))].slice(0, 10)
async function loadStatus() {
  statusError.value = ''
  try { status.value = await agentStatus() }
  catch { statusError.value = '无法连接后端，请启动 Flask 服务后重试。' }
}
function selectTool(call: ToolCall) { selected.value = call; pane.value = 'result'; panelOpen.value = true }
watch(activeId, () => { selected.value = undefined; panelOpen.value = false; input.value = ''; error.value = ''; scroll() })
async function scroll() { await nextTick(); log.value?.scrollTo({ top: log.value.scrollHeight, behavior: 'smooth' }) }
async function submit(value = input.value) {
  const question = value.trim()
  if (!question || busy.value || question.length > 4000) return
  busy.value = true
  error.value = ''
  const session = current.value
  const history = session.messages.slice(-12).map(m => ({ role: m.role, content: (m.content + (m.reply?.tool_calls.length ? '\n已执行工具结果：' + JSON.stringify(m.reply.tool_calls.map(c => ({ name: c.name, arguments: c.arguments, result: c.result }))) : '')).slice(0, 12000) }))
  session.messages.push({ id: crypto.randomUUID(), role: 'user', content: question })
  if (session.title === '新对话') session.title = question.slice(0, 60) + (question.length > 60 ? '…' : '')
  input.value = ''
  await scroll()
  try {
    const reply = await sendChat(question, history)
    session.messages.push({ id: crypto.randomUUID(), role: 'assistant', content: reply.answer, reply })
    selected.value = [...reply.tool_calls].reverse().find(c => c.name === 'aggregate_records' || c.name === 'calculate' || c.name === 'get_record') || reply.tool_calls.at(-1)
    panelOpen.value = reply.tool_calls.length > 0
    save()
  } catch {
    session.messages.pop()
    input.value = question
    error.value = '请求失败，问题已保留。请检查后端连接后重新发送。'
  } finally { busy.value = false; await scroll() }
}
function exportChat() {
  const text = '# ' + current.value.title + '\n\n' + current.value.messages.map(m => `## ${m.role === 'user' ? '你' : '原声 Agent'}\n\n${m.content}\n` + (m.reply ? `\n运行 ID：${m.reply.run_id}\n\n工具记录：\n\n\x60\x60\x60json\n${JSON.stringify(m.reply.tool_calls, null, 2)}\n\x60\x60\x60\n` : '')).join('\n')
  const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }))
  const a = document.createElement('a'); a.href = url; a.download = '原声分析对话.md'; a.click(); URL.revokeObjectURL(url)
}
onMounted(loadStatus)
</script>

<template>
  <div class="agent-page">
    <header class="workspace-header">
      <div class="header-title"><button class="icon-button mobile-menu" aria-label="打开导航" @click="toggleSidebar"><AppIcon name="menu" /></button><span class="breadcrumb">工作空间</span><AppIcon name="chevron" :size="13" /><span>对话分析</span></div>
      <div class="header-actions"><span class="mode-tag" :class="{ demo: status?.mode === 'demo' }">{{ status ? (status.mode === 'demo' ? '演示模式' : status.configured ? '模型已配置' : '待配置模型') : '连接中' }}</span><button class="text-button" @click="showTools = !showTools"><AppIcon name="settings" :size="15" />工具 {{ status?.tools.length || 0 }}</button><button class="icon-button" aria-label="切换分析依据面板" :aria-expanded="panelOpen" @click="panelOpen = !panelOpen"><AppIcon name="panel" /></button></div>
    </header>
    <div v-if="statusError" class="notice error" role="alert">{{ statusError }} <button @click="loadStatus">重试连接</button></div>
    <div v-else-if="status?.mode === 'demo'" class="notice">演示工作空间 · 使用 6 条虚构原声和固定规则。连接数据库与模型后可分析真实数据。</div>
    <div v-else-if="status && !status.configured" class="notice">在 backend/.env 配置 AGENT_API_KEY 后重启后端，即可启用对话分析。</div>
    <div v-if="showTools" class="tools-popover"><h3>Agent 可以调用的工具</h3><p v-for="tool in status?.tools" :key="tool.name"><strong>{{ toolNames[tool.name] }}</strong>{{ tool.description }}</p><small>工具仅查询和计算。导入、录入由数据管理页面完成。</small></div>
    <div class="agent-layout" :class="{ 'has-panel': panelOpen }">
      <section class="conversation" :class="{ 'is-empty': !current.messages.length }">
        <div class="conversation-toolbar"><h2>{{ current.title }}</h2><button class="text-button" :disabled="!current.messages.length || busy" @click="exportChat"><AppIcon name="export" :size="15" />导出对话</button></div>
        <div ref="log" class="message-log" role="log" aria-label="分析对话" :aria-busy="busy">
          <div v-if="!current.messages.length" class="welcome">
            <div class="welcome-mark"><AppIcon name="voice" :size="48" /></div>
            <h1>原声 Agent</h1>
            <p>让客户反馈成为洞察。今天想了解什么？</p>
          </div>
          <article v-for="m in current.messages" :key="m.id" class="message" :class="m.role">
            <div class="message-byline"><span class="avatar"><template v-if="m.role === 'user'">你</template><AppIcon v-else name="voice" :size="20" /></span><strong>{{ m.role === 'user' ? '你' : '原声 Agent' }}</strong><small v-if="m.reply">{{ m.reply.mode === 'demo' ? '演示工具流程' : '数据分析' }}</small></div>
            <div v-if="m.reply?.tool_calls.length" class="tool-steps"><button v-for="call in m.reply.tool_calls" :key="call.id" :class="{ failed: call.status === 'error', selected: selected?.id === call.id }" @click="selectTool(call)"><AppIcon :name="call.status === 'success' ? 'check' : 'close'" :size="13" />{{ toolNames[call.name] || call.name }}<small>{{ call.duration_ms }} ms</small></button></div>
            <p class="message-content">{{ m.content }}</p>
            <div v-if="m.role === 'assistant' && citations(m.content).length" class="citation-links"><button v-for="id in citations(m.content)" :key="id" :disabled="busy" @click="submit('查看原声 #' + id)">查看原声 #{{ id }}</button></div>
            <small v-if="m.reply && m.reply.status !== 'completed'" class="run-warning">本轮未完成 · {{ m.reply.status }}</small>
          </article>
          <div v-if="busy" class="working" role="status"><span class="working-dot"></span> 正在查询和分析，工具结果将在完成后显示…</div>
        </div>
        <div class="composer-area">
          <p v-if="error || storageError" class="inline-error" role="alert">{{ error || storageError }}</p>
          <div class="composer-mode"><AppIcon name="chat" :size="15" /><span>对话分析</span><span class="composer-mode-hint">可查询原声、统计和计算</span></div>
          <form class="composer" @submit.prevent="submit()">
            <label class="sr-only" for="question">向原声 Agent 提问</label><textarea id="question" v-model="input" maxlength="4000" placeholder="向原声提问，或输入一个分析任务…" :disabled="busy" rows="2" @keydown="e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !e.isComposing) { e.preventDefault(); submit() } }"></textarea>
            <div class="composer-bottom"><span class="composer-source"><AppIcon name="data" :size="14" />{{ status?.source || '等待数据连接' }}</span><div class="composer-submit"><span class="composer-model">{{ status?.mode === 'demo' ? '演示模式' : status?.model || '待配置模型' }}</span><button class="send-button" type="submit" :aria-label="busy ? '分析中' : '发送问题'" :disabled="busy || !input.trim() || !status?.configured"><AppIcon name="arrow" :size="17" /></button></div></div>
          </form>
          <div v-if="!current.messages.length" class="suggestions"><button v-for="(s, i) in suggestions" :key="s" :disabled="busy || !status?.configured" @click="submit(s)"><AppIcon :name="['chart', 'file', 'search', 'calculator'][i]!" :size="16" /><span>{{ ['品类分布', '差评分析', '查找原声', '数据计算'][i] }}</span></button></div>
          <div class="composer-note"><span>Ctrl / ⌘ + Enter 发送 · 结论请结合原声核对</span><button class="text-button" :disabled="busy" @click="clearChats">清空本地记录</button></div>
          <small class="privacy-note">最近 10 个对话保存在本浏览器，包含原声与工具结果。</small>
        </div>
      </section>
      <aside v-if="panelOpen" class="evidence-pane" aria-label="工具结果">
        <div class="evidence-heading"><div><AppIcon name="file" :size="17" /><h2>分析依据</h2><span>{{ calls.length }}</span></div><button class="icon-button" aria-label="关闭分析依据" @click="panelOpen = false"><AppIcon name="close" :size="17" /></button></div>
        <div class="evidence-tabs"><button :class="{ active: pane === 'result' }" @click="pane = 'result'">工具结果</button><button :class="{ active: pane === 'trace' }" @click="pane = 'trace'">执行记录</button></div>
        <div v-if="pane === 'trace'" class="trace-list"><p v-if="!calls.length" class="muted">发送问题后，这里会记录每次工具调用。</p><details v-for="call in calls" :key="call.id"><summary>{{ call.status === 'success' ? '✓' : '!' }} {{ toolNames[call.name] || call.name }}<small>{{ call.duration_ms }} ms</small></summary><h4>参数</h4><pre>{{ JSON.stringify(call.arguments, null, 2) }}</pre><h4>返回结果</h4><pre>{{ JSON.stringify(call.result, null, 2) }}</pre></details></div>
        <div v-else-if="selected" class="result-content">
          <div class="result-label"><span>{{ toolNames[selected.name] || selected.name }}</span><span :class="{ 'inline-error': selected.status === 'error' }">{{ selected.status === 'success' ? '已完成' : '执行失败' }}</span></div>
          <template v-if="selected.name === 'aggregate_records' && selected.status === 'success'"><h3>原声分布</h3><p class="muted">筛选范围内共 {{ selected.result.total }} 条</p><div v-for="g in groups" :key="g.label" class="bar-row"><div><span>{{ g.label }}</span><strong>{{ g.count }} <small>条</small></strong></div><div class="bar-track"><div :style="{ width: g.count / maxCount * 100 + '%' }"></div></div><small>占比 {{ g.share_percent }}%</small></div><p v-if="!groups.length" class="muted">没有符合条件的数据。</p><p class="result-footnote">{{ selected.result.denominator }}。{{ selected.result.truncated ? '仅显示前100组。' : '' }}</p></template>
          <template v-else-if="selected.name === 'search_records' && selected.status === 'success'"><h3>原声样本</h3><p class="muted">共 {{ selected.result.total }} 条，当前显示 {{ records.length }} 条</p><div v-for="r in records" :key="r.id" class="record-item"><strong>#{{ r.id }} <span>{{ r.platform }} / {{ r.category_l3 }}</span></strong><p>{{ r.text }}</p><button class="text-button" :disabled="busy" @click="submit('查看原声 #' + r.id)">查看详情</button></div><p v-if="!records.length" class="muted">没有符合条件的原声。</p></template>
          <template v-else-if="selected.name === 'calculate' && selected.status === 'success'"><h3>计算结果</h3><p class="formula">{{ selected.result.expression }}</p><div class="calculation-value">{{ selected.result.value }}</div></template>
          <template v-else-if="selected.name === 'get_record' && selected.result.text"><h3>原声 #{{ selected.result.id }}</h3><p class="muted">{{ selected.result.platform }} / {{ selected.result.category_l3 }}</p><blockquote>{{ selected.result.text }}</blockquote><pre v-if="selected.result.analysis">{{ JSON.stringify(selected.result.analysis, null, 2) }}</pre></template>
          <template v-else><h3>{{ selected.status === 'error' ? '请调整后重试' : '数据说明' }}</h3><pre>{{ JSON.stringify(selected.result, null, 2) }}</pre></template>
          <details class="result-parameters"><summary>查看本次筛选与参数</summary><pre>{{ JSON.stringify(selected.arguments, null, 2) }}</pre></details>
        </div>
        <div v-else class="evidence-empty"><div class="document-icon"><AppIcon name="file" :size="32" /></div><h3>答案背后的数据</h3><p>统计分布、原声样本和计算结果<br>会随对话出现在这里。</p><div class="evidence-example"><span>提问</span><p>“京东有哪些差评？”</p><span>获取依据</span><p>筛选数据 → 查看原声 → 汇总结论</p></div></div>
        <div class="evidence-footer"><AppIcon name="shield" :size="14" />只读工具，保留查询依据</div>
      </aside>
    </div>
  </div>
</template>
