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

export interface ImportRowError {
  row: number
  error: string
}

export interface ImportResult {
  imported: number
  errors: ImportRowError[]
  total: number
  catalog_matched?: number
  catalog_unmatched?: number
}

export async function uploadDatasetFile(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post<ImportResult>('/dataset/import', form)
  return data
}

export interface DatasetRecordInput {
  product_id: string
  customer_transcript: string
  [key: string]: string | number | boolean | null | undefined
}

export interface DatasetRecordResult {
  id: number
  source_product_id: string
  sku: string
  category_l1: string
  category_l2: string
  category_l3: string
  catalog_matched: boolean
}

export async function createDatasetRecord(payload: DatasetRecordInput): Promise<DatasetRecordResult> {
  const { data } = await http.post<DatasetRecordResult>('/dataset/record', payload)
  return data
}

export interface AnalysisError {
  dataset_info_id: number
  error: string
}

export interface AnalysisRunResult {
  requested: number
  analyzed: number
  failed: number
  remaining: number
  errors: AnalysisError[]
}

export async function runComplaintAnalysis(limit = 100): Promise<AnalysisRunResult> {
  const { data } = await http.post<AnalysisRunResult>('/analysis/run', { limit }, {
    timeout: 10 * 60 * 1000,
  })
  return data
}

export interface ReviewListParams {
  category_l1?: string; category_l2?: string; category_l3?: string; sku?: string
  touchpoint?: string; platform?: string; function_tag_l1?: string
  evaluation_level?: string; emotion_dimension?: string; problem_nature?: string; appeal_intent?: string
  analysis_status?: 'all' | 'analyzed' | 'pending'; page?: number; page_size?: number
  sort_by?: 'id' | 'created_at'; sort_order?: 'asc' | 'desc'
}

export interface ReviewListItem {
  dataset_info_id: number; category_l1: string; category_l2: string; category_l3: string
  sku: string; touchpoint: string; platform: string; function_tag_l1: string | null
  evaluation_level: string | null; emotion_dimension: string | null; problem_nature: string | null; appeal_intent: string | null
  analysis_status: 'analyzed' | 'pending'
}

export interface ReviewListResponse {
  items: ReviewListItem[]; total: number; page: number; page_size: number; pages: number
}

export interface ReviewDetail { dataset_info: Record<string, unknown>; analysis_result: Record<string, unknown> | null }

export async function fetchReviews(params: ReviewListParams = {}): Promise<ReviewListResponse> {
  const { data } = await http.get<ReviewListResponse>('/reviews', { params })
  return data
}

export async function fetchReviewDetail(id: number): Promise<ReviewDetail> {
  const { data } = await http.get<ReviewDetail>(`/reviews/${id}`)
  return data
}

export default http
