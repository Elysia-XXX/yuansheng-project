<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchHealth, type HealthResponse } from '../api'

interface ServiceStatus {
  name: string
  status: string
  detail: string
}

const loading = ref(true)
const services = ref<ServiceStatus[]>([])

async function loadHealth() {
  loading.value = true
  try {
    const data: HealthResponse = await fetchHealth()
    services.value = [
      {
        name: 'Flask 后端',
        status: data.status,
        detail: data.service,
      },
      {
        name: 'PostgreSQL 数据库',
        status: data.database,
        detail: data.database_error || '连接正常',
      },
    ]
  } catch (err) {
    services.value = [
      {
        name: 'Flask 后端',
        status: 'error',
        detail: '无法连接后端，请确认后端已启动（python run.py）',
      },
      {
        name: 'PostgreSQL 数据库',
        status: 'unknown',
        detail: String(err),
      },
    ]
  } finally {
    loading.value = false
  }
}

function statusType(status: string): 'success' | 'danger' | 'info' {
  if (status === 'ok') return 'success'
  if (status === 'error') return 'danger'
  return 'info'
}

onMounted(loadHealth)
</script>

<template>
  <div class="home">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>系统状态</span>
          <el-button size="small" :loading="loading" @click="loadHealth">
            刷新
          </el-button>
        </div>
      </template>

      <div v-loading="loading">
        <el-descriptions v-if="services.length" :column="1" border>
          <el-descriptions-item
            v-for="item in services"
            :key="item.name"
            :label="item.name"
          >
            <el-tag :type="statusType(item.status)" size="small">
              {{ item.status }}
            </el-tag>
            <span class="detail">{{ item.detail }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.home {
  max-width: 720px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail {
  margin-left: 12px;
  color: #909399;
  word-break: break-all;
}
</style>
