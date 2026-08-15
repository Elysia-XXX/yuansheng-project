<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchReviewDetail, fetchReviews, type ReviewDetail, type ReviewListItem } from '../api'

const loading = ref(false)
const detailLoading = ref(false)
const rows = ref<ReviewListItem[]>([])
const total = ref(0)
const pages = ref(0)
const detailVisible = ref(false)
const detail = ref<ReviewDetail | null>(null)
const query = reactive<Record<string, any>>({
  category_l1: '', category_l2: '', category_l3: '', sku: '', touchpoint: '', platform: '',
  function_tag_l1: '', evaluation_level: '', emotion_dimension: '', problem_nature: '', appeal_intent: '', analysis_status: 'all',
  page: 1, page_size: 20, sort_by: 'id', sort_order: 'desc',
})

const fixed = {
  category_l1: ['厨电', '生活小家电', '个护健康', '其他'], touchpoint: ['S1', 'S2', 'S3', 'S4', 'S5'],
  platform: ['天猫', '京东', '淘宝', '抖音', '拼多多', '微信小程序', '快手', '其他'],
  evaluation_level: ['好评', '中评', '差评', '疑问', '无意义'], emotion_dimension: ['快乐', '悲伤', '愤怒', '恐惧', '厌恶'], problem_nature: ['质量问题', '功能问题', '体验问题', '服务问题', '物流问题', '其他'],
  appeal_intent: ['退货退款', '换货维修', '咨询原因', '改进建议', '情绪表达', '其他'],
}
const options = (field: string) => computed(() => Array.from(new Set([...(fixed as any)[field] || [], ...rows.value.map((row: any) => row[field]).filter(Boolean)])))
const categoryL1Options = options('category_l1'); const categoryL2Options = options('category_l2'); const categoryL3Options = options('category_l3'); const skuOptions = options('sku')
const functionOptions = options('function_tag_l1')
const labels: Record<string, string> = {
  id: '记录 ID', source_product_id: '商品 ID', customer_transcript: '客户原文', touchpoint: '触点渠道', source_form: '来源形态',
  category_l1: '一级分类', category_l2: '二级分类', category_l3: '三级分类', sku: 'SKU', region: '大区', province: '省份',
  city_tier: '城市线级', gender: '性别', age: '年龄', use_scene: '使用场景', user_type: '用户类型', member_level: '会员等级',
  price_band: '价格带', paid_amount: '实付金额', original_amount: '原价金额', platform: '购买平台', promo_type: '促销类型',
  warranty_status: '质保状态', is_gift: '是否赠品', complaint_time: '投诉时间', duration_to_complaint: '到客诉时长',
  product_season: '产品季节', complaint_season: '客诉季节', lifecycle_stage: '生命周期', created_at: '创建时间',
  function_tag_l1: '功能一级标签', function_tag_l2: '功能二级标签', production_stage: '生产环节', production_substage: '生产子环节',
  part_category: '部件大类', part_name: '具体部件', evaluation_level: '评价等级', emotion_dimension: '情绪五维', problem_nature: '问题性质',
  keyword_cluster: '关键词簇', appeal_intent: '诉求意图',
}

async function load() {
  loading.value = true
  try {
    const data = await fetchReviews(query)
    rows.value = data.items; total.value = data.total; pages.value = data.pages
  } catch (error: any) { ElMessage.error(error?.response?.data?.error || '评论列表加载失败') } finally { loading.value = false }
}
function search() { query.page = 1; load() }
function reset() { Object.assign(query, { category_l1: '', category_l2: '', category_l3: '', sku: '', touchpoint: '', platform: '', function_tag_l1: '', evaluation_level: '', emotion_dimension: '', problem_nature: '', appeal_intent: '', analysis_status: 'all', page: 1 }); load() }
async function openDetail(id: number) {
  detailVisible.value = true; detailLoading.value = true; detail.value = null
  try { detail.value = await fetchReviewDetail(id) } catch (error: any) { ElMessage.error(error?.response?.data?.error || '详情加载失败'); detailVisible.value = false } finally { detailLoading.value = false }
}
function value(obj: Record<string, unknown> | undefined, key: string) { const item = obj?.[key]; return item === null || item === undefined || item === '' ? '未填写' : Array.isArray(item) ? item.join('、') || '未填写' : String(item) }
function label(key: string) { return labels[key] || key }
onMounted(load)
</script>

<template>
  <div class="page">
    <el-card shadow="never" class="filter-card">
      <template #header><div class="header"><span>客户评价管理</span><el-button size="small" @click="load">刷新</el-button></div></template>
      <el-form inline @submit.prevent="search">
        <el-form-item label="一级分类"><el-select v-model="query.category_l1" clearable filterable placeholder="全部" style="width: 145px"><el-option v-for="v in categoryL1Options" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="二级分类"><el-select v-model="query.category_l2" clearable filterable placeholder="全部" style="width: 145px"><el-option v-for="v in categoryL2Options" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="三级分类"><el-select v-model="query.category_l3" clearable filterable placeholder="全部" style="width: 145px"><el-option v-for="v in categoryL3Options" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="SKU"><el-select v-model="query.sku" clearable filterable allow-create placeholder="全部" style="width: 155px"><el-option v-for="v in skuOptions" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="触点"><el-select v-model="query.touchpoint" clearable placeholder="全部" style="width: 120px"><el-option v-for="v in fixed.touchpoint" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="平台"><el-select v-model="query.platform" clearable placeholder="全部" style="width: 130px"><el-option v-for="v in fixed.platform" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="功能标签"><el-select v-model="query.function_tag_l1" clearable filterable allow-create placeholder="全部" style="width: 160px"><el-option v-for="v in functionOptions" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="评价等级"><el-select v-model="query.evaluation_level" clearable placeholder="全部" style="width: 120px"><el-option v-for="v in fixed.evaluation_level" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="情绪五维"><el-select v-model="query.emotion_dimension" clearable placeholder="全部" style="width: 115px"><el-option v-for="v in fixed.emotion_dimension" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="问题性质"><el-select v-model="query.problem_nature" clearable placeholder="全部" style="width: 130px"><el-option v-for="v in fixed.problem_nature" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="诉求"><el-select v-model="query.appeal_intent" clearable placeholder="全部" style="width: 130px"><el-option v-for="v in fixed.appeal_intent" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="分析状态"><el-select v-model="query.analysis_status" style="width: 120px"><el-option label="全部" value="all" /><el-option label="已分析" value="analyzed" /><el-option label="待分析" value="pending" /></el-select></el-form-item>
        <el-form-item label="排序"><el-select v-model="query.sort_by" style="width: 120px"><el-option label="按 ID" value="id" /><el-option label="按创建时间" value="created_at" /></el-select><el-select v-model="query.sort_order" style="width: 100px; margin-left: 6px"><el-option label="降序" value="desc" /><el-option label="升序" value="asc" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="search">查询</el-button><el-button @click="reset">重置</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" v-loading="loading" class="table-card">
      <el-table :data="rows" stripe border empty-text="暂无评论">
        <el-table-column prop="dataset_info_id" label="ID" width="78" />
        <el-table-column prop="category_l1" label="一级分类" width="105" />
        <el-table-column prop="category_l2" label="二级分类" width="105" />
        <el-table-column prop="category_l3" label="三级分类" width="115" />
        <el-table-column prop="sku" label="SKU" width="145" show-overflow-tooltip />
        <el-table-column prop="touchpoint" label="触点" width="90" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column prop="function_tag_l1" label="功能标签" min-width="130" show-overflow-tooltip />
        <el-table-column prop="evaluation_level" label="评价等级" width="100" />
        <el-table-column prop="emotion_dimension" label="情绪五维" width="95" />
        <el-table-column prop="problem_nature" label="问题性质" width="105" />
        <el-table-column prop="appeal_intent" label="诉求" width="105" />
        <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.analysis_status === 'analyzed' ? 'success' : 'warning'">{{ row.analysis_status === 'analyzed' ? '已分析' : '待分析' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" fixed="right" width="85"><template #default="{ row }"><el-button link type="primary" @click="openDetail(row.dataset_info_id)">详情</el-button></template></el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next" :total="total" @current-change="load" @size-change="search" /></div>
    </el-card>

    <el-drawer v-model="detailVisible" title="客户评价详情" size="620px">
      <div v-loading="detailLoading" v-if="detail">
        <h3>客户评价</h3><el-descriptions :column="1" border><el-descriptions-item :label="label('customer_transcript')">{{ value(detail.dataset_info, 'customer_transcript') }}</el-descriptions-item></el-descriptions>
        <h3>商品与分类</h3><el-descriptions :column="2" border><el-descriptions-item v-for="key in ['id','source_product_id','category_l1','category_l2','category_l3','sku','touchpoint','source_form']" :key="key" :label="label(key)">{{ value(detail.dataset_info, key) }}</el-descriptions-item></el-descriptions>
        <h3>客户画像</h3><el-descriptions :column="2" border><el-descriptions-item v-for="key in ['region','province','city_tier','gender','age','use_scene','user_type','member_level']" :key="key" :label="label(key)">{{ value(detail.dataset_info, key) }}</el-descriptions-item></el-descriptions>
        <h3>订单交易与生命周期</h3><el-descriptions :column="2" border><el-descriptions-item v-for="key in ['price_band','paid_amount','original_amount','platform','promo_type','warranty_status','is_gift','complaint_time','duration_to_complaint','product_season','complaint_season','lifecycle_stage','created_at']" :key="key" :label="label(key)">{{ value(detail.dataset_info, key) }}</el-descriptions-item></el-descriptions>
        <h3>大模型分析结果</h3><el-empty v-if="!detail.analysis_result" description="尚未完成分析" /><el-descriptions v-else :column="2" border><el-descriptions-item v-for="key in ['function_tag_l1','function_tag_l2','production_stage','production_substage','part_category','part_name','evaluation_level','emotion_dimension','problem_nature','keyword_cluster','appeal_intent','created_at']" :key="key" :label="label(key)">{{ value(detail.analysis_result, key) }}</el-descriptions-item></el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.page { max-width: 1500px; margin: 0 auto; }
.filter-card, .table-card { margin-top: 18px; }
.header { display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 600; }
.pagination { display: flex; justify-content: flex-end; margin-top: 18px; }
h3 { margin: 22px 0 10px; font-size: 15px; color: #303133; }
</style>
