import http from './index'

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown> | null
  result: Record<string, unknown>
  status: 'success' | 'error'
  duration_ms: number
}
export interface AgentStatus {
  mode: 'demo' | 'model'
  configured: boolean
  source: string
  model: string | null
  tools: { name: string; description: string }[]
}
export interface AgentReply {
  run_id: string
  mode: 'demo' | 'model'
  answer: string
  status: string
  tool_calls: ToolCall[]
}
export const agentStatus = async () => (await http.get<AgentStatus>('/agent/status')).data
export const sendChat = async (message: string, history: { role: string; content: string }[]) =>
  (await http.post<AgentReply>('/agent/chat', { message, history }, { timeout: 110000 })).data
