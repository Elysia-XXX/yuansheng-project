import axios from 'axios'

/**
 * 统一 axios 实例：baseURL 为 /api，开发环境由 Vite 代理转发到后端
 */
const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface HealthResponse {
  status: string
  service: string
  database: string
  database_error: string | null
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await http.get<HealthResponse>('/health')
  return data
}

export default http
