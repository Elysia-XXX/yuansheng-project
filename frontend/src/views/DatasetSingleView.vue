<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createDatasetRecord, type DatasetRecordInput, type DatasetRecordResult } from '../api'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const result = ref<DatasetRecordResult | null>(null)

const form = reactive<Record<string, string | number | boolean | null>>({
  product_id: '', customer_transcript: '', touchpoint: '', source_form: '',
  region: '', province: '', city_tier: '', gender: '', age: '', use_scene: '',
  user_type: '', member_level: '', price_band: '', paid_amount: '', original_amount: '',
  platform: '', promo_type: '', warranty_status: '', is_gift: '', complaint_time: '',
  duration_to_complaint: '', product_season: '', complaint_season: '', lifecycle_stage: '',
})

const rules: FormRules = {
  product_id: [{ required: true, message: '请输入商品 ID', trigger: 'blur' }],
  customer_transcript: [{ required: true, message: '请输入客户评价具体内容', trigger: 'blur' }],
}

const radios = {
  touchpoint: ['S1 客服咨询', 'S2 商品评价', 'S3 退货原因', 'S4 问答', 'S5 投诉/申诉'],
  gender: ['女', '男', '未知（家庭共用）'], city_tier: ['一线', '新一线', '二线', '三线', '四线'],
  user_type: ['新客（首购）', '老客', '复购', '流失召回'], member_level: ['非会员', '普通会员', '银卡', '金卡', '钻石', 'PLUS'],
  price_band: ['100 元以下', '100-299 元', '300-599 元', '600-999 元', '1000 元及以上'],
  platform: ['天猫', '京东', '抖音', '拼多多', '淘宝', '微信小程序', '快手', '其他'],
  warranty_status: ['7 天无理由', '1 年质保期内', '质保期外'], product_season: ['春季', '夏季', '秋季', '冬季', '平季'],
  complaint_season: ['春', '夏', '秋', '冬'],
  lifecycle_stage: ['购买前_咨询', '到货_开箱', '首次使用', '短期使用_30天内', '中期使用_1年内', '售后维修', '退货中'],
}
const radioSections = [
  ['gender', '性别', radios.gender], ['city_tier', '城市线级', radios.city_tier], ['user_type', '用户类型', radios.user_type],
  ['member_level', '会员等级', radios.member_level], ['price_band', '价格带', radios.price_band], ['warranty_status', '质保状态', radios.warranty_status],
  ['product_season', '产品季节', radios.product_season], ['complaint_season', '客诉季节', radios.complaint_season], ['lifecycle_stage', '生命周期', radios.lifecycle_stage],
] as const

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  result.value = null
  try {
    const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== '' && value !== null)) as DatasetRecordInput
    result.value = await createDatasetRecord(payload)
    ElMessage.success('单条数据已写入')
    form.customer_transcript = ''
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.error || '写入失败，请检查后端服务')
  } finally { submitting.value = false }
}
</script>

<template>
  <div class="page"><el-card class="card">
    <template #header><div class="title">单条客户评价录入</div></template>
    <p class="hint">仅商品 ID和客户评价具体内容必填，其余字段可留空；目录中存在商品时会自动补齐 SKU 和一二三级分类。</p>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="150px" @submit.prevent="submit">
      <el-form-item label="商品 ID" prop="product_id"><el-input v-model="form.product_id" placeholder="例如 1002774162126" clearable /></el-form-item>
      <el-form-item label="客户评价具体内容" prop="customer_transcript"><el-input v-model="form.customer_transcript" type="textarea" :rows="4" placeholder="请输入客户原话" /></el-form-item>

      <el-divider content-position="left">可选信息</el-divider>
      <el-row :gutter="18">
        <el-col :xs="24" :md="12"><el-form-item label="触点渠道"><el-radio-group v-model="form.touchpoint"><el-radio label="">不填写</el-radio><el-radio v-for="v in radios.touchpoint" :key="v" :label="v" /></el-radio-group></el-form-item></el-col>
        <el-col :xs="24" :md="12"><el-form-item label="购买平台"><el-radio-group v-model="form.platform"><el-radio label="">不填写</el-radio><el-radio v-for="v in radios.platform" :key="v" :label="v" /></el-radio-group></el-form-item></el-col>
      </el-row>
      <el-row v-for="[field, label, items] in radioSections" :key="field" :gutter="18">
        <el-col :span="24"><el-form-item :label="label"><el-radio-group v-model="form[field]"><el-radio label="">不填写</el-radio><el-radio v-for="v in items" :key="v" :label="v" /></el-radio-group></el-form-item></el-col>
      </el-row>
      <el-row :gutter="18">
        <el-col :xs="24" :md="8"><el-form-item label="来源形态"><el-input v-model="form.source_form" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="地区"><el-input v-model="form.region" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="省份"><el-input v-model="form.province" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="年龄"><el-input v-model="form.age" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="使用场景"><el-input v-model="form.use_scene" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="促销类型"><el-input v-model="form.promo_type" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="实付金额"><el-input-number v-model="form.paid_amount" :min="0" :precision="2" controls-position="right" /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="原价"><el-input-number v-model="form.original_amount" :min="0" :precision="2" controls-position="right" /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="客诉时间"><el-date-picker v-model="form.complaint_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="到客诉时长"><el-input v-model="form.duration_to_complaint" placeholder="例如 7天" clearable /></el-form-item></el-col>
        <el-col :xs="24" :md="8"><el-form-item label="是否赠品"><el-radio-group v-model="form.is_gift"><el-radio label="">不填写</el-radio><el-radio :label="true">是</el-radio><el-radio :label="false">否</el-radio></el-radio-group></el-form-item></el-col>
      </el-row>
      <div class="actions"><el-button type="primary" :loading="submitting" @click="submit">提交这一条</el-button><el-button @click="formRef?.resetFields(); result = null">清空</el-button></div>
    </el-form>
    <el-alert v-if="result" class="result" type="success" :closable="false" title="写入成功">
      <template #default>记录 ID：{{ result.id }}；SKU：{{ result.sku }}；分类：{{ result.category_l1 }} / {{ result.category_l2 }} / {{ result.category_l3 }}</template>
    </el-alert>
  </el-card></div>
</template>

<style scoped>
.page { max-width: 1100px; margin: 0 auto; }
.card { margin-top: 18px; }
.title { font-size: 18px; font-weight: 600; }
.hint { color: #909399; margin: 0 0 20px; }
.el-radio-group { display: flex; flex-wrap: wrap; gap: 4px 12px; }
.actions { text-align: center; margin-top: 12px; }
.result { margin-top: 20px; }
</style>
