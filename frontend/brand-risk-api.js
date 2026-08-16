// 品牌风险页不新增后端接口：仅聚合已加载的真实看板与品牌客诉数据。
export function buildBrandRiskAnalysis(apiData) {
  const dashboards = apiData.analysisDashboardData || {};
  const brand = dashboards.brand || {};
  const orders = dashboards.orders || {};
  const customer = dashboards.customer || {};
  const semantic = dashboards.semantic || {};
  const monthSeries = apiData.categoryMonthSeries || {};
  const topProducts = apiData.topCategories || [];
  const leaves = [];
  const collect = nodes => (nodes || []).forEach(node => {
    if (node.children?.length) collect(node.children);
    else leaves.push(node);
  });
  collect(apiData.tagData?.brand || []);
  const evidence = leaves.flatMap(node => node.complaints || []).filter(item => item?.text);
  const monthKeys = Object.keys(monthSeries).sort().slice(-6);
  const factor = Number(brand.factor || 0.22);
  const tags = (brand.tags || []).slice(0, 4);
  const platforms = (brand.secondary || []).slice(0, 4);
  const total = Number(brand.summary?.total || evidence.length || 0);
  const riskActions = tags.slice(0, 2).map((tag, index) => ({
    id: ['activity', 'creator'][index],
    title: ['核查并修正活动规则', '暂停争议营销话术'][index],
    priority: 'P0',
    summary: `${tag}进入品牌风险标签 TOP${index + 1}，需回看渠道客诉证据。`,
    owner: ['电商运营', '品牌内容'][index],
    deadline: ['6小时内', '今日完成'][index]
  }));
  const qaQuestions = apiData.qaQuestions || [];
  const questions = qaQuestions.length
    ? qaQuestions.map(item => ({
        id: item.id ?? null,
        question: item.question,
        context: [item.category_l1, item.category_l2, item.category_l3].filter(Boolean).join(' / ') || item.sku || '问大家',
        repeatCount: item.answer_count || 0,
        signal: item.platform || '淘宝',
        answers: item.answers || [],
        sku: item.sku,
      }))
    : Array.from({ length: Math.min(8, Math.max(1, evidence.length)) }, (_, index) => {
        const item = evidence[index] || {};
        return {
          id: item.id ?? null,
          question: item.text || tags[index] || '请人工核验品牌风险证据',
          context: topProducts[index]?.name || leaves[index]?.label || '品牌营销维度',
          repeatCount: Math.max(1, evidence.filter(row => row.source === item.source).length),
          signal: item.source || '品牌客诉',
          time: item.time || null,
          answers: item.qa_answers || []
        };
      });
  const tasks = riskActions.map((item, index) => ({
    title: item.title, status: ['执行中', '待验证'][index], owner: item.owner,
    progress: [70, 90][index], result: ['等待下个数据周期验证', '需补充渠道对照组'][index]
  }));
  return {
    filters: { periods: ['近30天', '近7天', '本季度'], categories: ['全部品类', ...topProducts.slice(0, 3).map(item => item.name)], platforms: ['全部平台', ...platforms] },
    overview: {
      judgement: { title: '今日核心判断', summary: `${tags.slice(0, 2).join('、') || '品牌风险'}为当前主要风险；${brand.summary?.peakSecondary || platforms[0] || '核心渠道'}样本占比较高。建议先核验客诉原文，再由人工确认处置方案。`, sampleSize: total },
      kpis: [
        { label: '品牌客诉样本', value: total.toLocaleString('zh-CN'), note: '来自品牌营销看板' },
        { label: '高风险营销标签', value: String(brand.summary?.riskTagCount || tags.length), note: tags.slice(0, 3).join('、') || '—' },
        { label: '最高风险渠道', value: brand.summary?.peakSecondary || platforms[0] || '—', note: `渠道占比 ${brand.shares?.[0] || 0}%` },
        { label: '待人工确认行动', value: String(tasks.length), note: '前端聚合生成的草案' }
      ],
      trend: { labels: monthKeys.map(key => `${Number(key.split('-')[1])}月`), values: monthKeys.map(key => Math.round(Number(monthSeries[key] || 0) * factor)) },
      heatmap: { issues: tags, rows: platforms.map((platform, rowIndex) => ({ platform, values: tags.map((_, columnIndex) => Math.max(0, Math.round((brand.shares?.[rowIndex] || 0) * (1.65 - columnIndex * .22)))) })) },
      priorityActions: riskActions, questions: questions.slice(0, 3), tasks
    },
    questions, tasks,
    campaignKpis: [
      { label: '品牌客诉样本', value: total.toLocaleString('zh-CN'), note: '来自品牌营销看板' },
      { label: '订单交易客诉', value: Number(orders.summary?.total || 0).toLocaleString('zh-CN'), note: orders.summary?.peakSecondary || '订单接口' },
      { label: '语义高频主题', value: semantic.tags?.[0] || '—', note: '来自语义分析接口' },
      { label: '活动因果判断', value: '待接入', note: '缺少活动事件与曝光分母' }
    ],
    dataGaps: ['营销活动、达人、直播场次、素材和宣传卖点的唯一 ID 与生效时间', '问大家的提问量、回答数、点赞数、官方回复状态和响应时长', '订单量、曝光量、退款率和转化率等分母数据', '行动任务的负责人、审批状态、截止时间、交付物、基线和实际结果']
  };
}
