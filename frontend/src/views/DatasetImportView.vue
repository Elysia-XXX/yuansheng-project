<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  runComplaintAnalysis,
  uploadDatasetFile,
  type AnalysisRunResult,
  type ImportResult,
  type ImportRowError,
} from '../api'

const fileList = ref<File[]>([])
const uploading = ref(false)
const result = ref<ImportResult | null>(null)
const errorRows = ref<ImportRowError[]>([])
const analyzing = ref(false)
const analysisResult = ref<AnalysisRunResult | null>(null)

function beforeUpload(file: File): boolean {
  if (!file.name.toLowerCase().endsWith('.xlsx')) {
    ElMessage.error('仅支持 .xlsx 文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件不能超过 10MB')
    return false
  }
  return true
}

async function handleAnalysis() {
  analyzing.value = true
  analysisResult.value = null
  try {
    const res = await runComplaintAnalysis()
    analysisResult.value = res
    if (res.analyzed > 0) {
      ElMessage.success(`已完成 ${res.analyzed} 条客诉分析`)
    } else if (res.failed > 0) {
      ElMessage.error('本批次分析失败，请查看错误详情')
    } else {
      ElMessage.info('没有待分析的数据')
    }
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
    ElMessage.error(detail || '智能分析失败，请检查大模型配置和后端日志')
  } finally {
    analyzing.value = false
  }
}

function onFileChange(uploadFile: { raw: File }) {
  const raw = uploadFile.raw
  if (!beforeUpload(raw)) return
  fileList.value = [raw]
}

function onExceed() {
  ElMessage.warning('每次只能上传一个文件，请先移除再选择')
}

async function handleUpload() {
  const file = fileList.value[0]
  if (!file) {
    ElMessage.warning('请先选择 xlsx 文件')
    return
  }
  uploading.value = true
  result.value = null
  errorRows.value = []
  try {
    const res = await uploadDatasetFile(file)
    result.value = res
    errorRows.value = res.errors
    if (res.imported > 0) {
      ElMessage.success(`成功导入 ${res.imported} 条记录`)
    } else {
      ElMessage.warning('没有数据被导入')
    }
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
    ElMessage.error(detail || '导入失败，请检查后端服务是否正常')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="import-page">
    <el-card shadow="never">
      <template #header>
        <span>数据集导入</span>
      </template>

      <p class="tip">
        上传 <code>.xlsx</code> 文件（支持原来的中文表头+英文字段名两行模板，也支持只含
        <code>product_id</code> / “商品id” 的简化模板），数据将写入 <code>dataset_info</code> 表。
        商品 ID 会从商品目录自动补齐 SKU 和一/二/三级品类；其他字段可选填。
      </p>

      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx"
        :on-change="onFileChange"
        :on-exceed="onExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload">
          <svg viewBox="0 0 1024 1024" width="64" height="64">
            <path fill="currentColor" d="M512 640c-20 0-40-8-54-23L231 384h102l70 70V128h218v326l70-70h102L566 617c-14 15-34 23-54 23zm256-384v512H256V256h128V128H128v768h768V128H640v128z"/>
          </svg>
        </el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">仅支持 xlsx，大小不超过 10MB</div>
        </template>
      </el-upload>

      <div class="actions">
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          {{ uploading ? '导入中…' : '开始导入' }}
        </el-button>
      </div>

      <div v-if="result" class="result">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="总计">
            {{ result.total }}
          </el-descriptions-item>
          <el-descriptions-item label="成功导入">
            <el-tag type="success" size="small">{{ result.imported }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="错误行">
            <el-tag v-if="errorRows.length" type="danger" size="small">
              {{ errorRows.length }}
            </el-tag>
            <span v-else>0</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="result.catalog_matched !== undefined" label="目录匹配">
            {{ result.catalog_matched }}
          </el-descriptions-item>
          <el-descriptions-item v-if="result.catalog_unmatched" label="目录未匹配">
            <el-tag type="warning" size="small">{{ result.catalog_unmatched }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-table v-if="errorRows.length" :data="errorRows" border class="error-table">
          <el-table-column prop="row" label="Excel 行号" width="120" />
          <el-table-column prop="error" label="错误原因" />
        </el-table>
      </div>
    </el-card>

    <el-card shadow="never" class="analysis-card">
      <template #header>
        <span>客诉智能分析</span>
      </template>
      <p class="tip">
        调用 Xiaomi MiMo，对尚未生成结果的 <code>dataset_info</code> 数据进行结构化整理，并写入
        <code>analysis_result</code> 表。每次最多处理 100 条，已分析数据会自动跳过。
      </p>
      <el-button type="success" :loading="analyzing" @click="handleAnalysis">
        {{ analyzing ? '分析中，请勿关闭页面…' : '开始智能分析' }}
      </el-button>

      <el-descriptions v-if="analysisResult" :column="4" border class="analysis-result">
        <el-descriptions-item label="本批读取">{{ analysisResult.requested }}</el-descriptions-item>
        <el-descriptions-item label="成功">
          <el-tag type="success" size="small">{{ analysisResult.analyzed }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="失败">
          <el-tag :type="analysisResult.failed ? 'danger' : 'info'" size="small">{{ analysisResult.failed }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="剩余">{{ analysisResult.remaining }}</el-descriptions-item>
      </el-descriptions>
      <el-table
        v-if="analysisResult?.errors.length"
        :data="analysisResult.errors"
        border
        class="error-table"
      >
        <el-table-column prop="dataset_info_id" label="数据 ID" width="120" />
        <el-table-column prop="error" label="错误原因" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.import-page {
  max-width: 720px;
  margin: 0 auto;
}

.tip {
  color: #606266;
  line-height: 1.7;
}

.tip code {
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.actions {
  margin-top: 16px;
}

.result {
  margin-top: 20px;
}

.error-table {
  margin-top: 16px;
}

.analysis-card {
  margin-top: 20px;
}

.analysis-result {
  margin-top: 20px;
}
</style>
