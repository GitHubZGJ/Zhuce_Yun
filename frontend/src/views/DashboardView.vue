<template>
  <div class="page" v-loading="loading">
    <div class="page-head">
      <div>
        <div class="page-kicker">OPERATIONS OVERVIEW</div>
        <h1 class="page-title">数据看板</h1>
        <p class="page-sub">
          {{ greeting }}，{{ auth.user?.display_name }}。今日汇总 {{ summary.project_total }} 个工程项目与
          {{ summary.test_total }} 条检测记录，质量态势如下。
        </p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="loadAll">刷新数据</el-button>
        <el-button type="primary" :icon="Plus" @click="router.push('/test-records')">录入检测</el-button>
      </div>
    </div>

    <div class="hero-strip">
      <div>
        <div class="hero-kicker">QUALITY CONTROL ROOM · {{ todayLabel }}</div>
        <div class="hero-title">工程质量态势 · 实时汇总</div>
        <div class="hero-sub">
          当前有 {{ summary.active_projects }} 个在建项目、{{ summary.pending_samples }} 个待检样品；
          累计 {{ summary.open_defect_occurrences }} 次待修复缺陷，AI 协作可靠性
          {{ summary.reliability }} 分。
        </div>
      </div>
      <div class="hero-metrics">
        <div class="hero-metric">
          <strong class="num">{{ summary.active_projects }}</strong>
          <span>在建项目</span>
        </div>
        <div class="hero-metric">
          <strong class="num">{{ summary.pending_samples }}</strong>
          <span>待检样品</span>
        </div>
        <div class="hero-metric">
          <strong class="num">{{ summary.open_defect_occurrences }}</strong>
          <span>待修复缺陷</span>
        </div>
        <div class="hero-metric">
          <strong class="num">{{ summary.reliability }}</strong>
          <span>AI 可靠性</span>
        </div>
      </div>
    </div>

    <div class="kpi-grid">
      <StatCard
        label="工程项目总数"
        :value="summary.project_total"
        unit="个"
        icon="OfficeBuilding"
        :hint="`${summary.active_projects} 个在建 · ${summary.project_total - summary.active_projects} 个其他状态`"
      />
      <StatCard
        label="检测记录总数"
        :value="summary.test_total"
        unit="条"
        icon="DataAnalysis"
        tone="teal"
        :hint="`合格 ${summary.pass_total} 条 · 不合格 ${summary.test_total - summary.pass_total} 条`"
      />
      <StatCard
        label="总体合格率"
        :value="Number(summary.pass_rate).toFixed(1)"
        unit="%"
        icon="CircleCheck"
        tone="green"
      >
        <span class="up">达标</span>
        <span>按已判定记录计算</span>
      </StatCard>
      <StatCard
        label="AI 协作可靠性"
        :value="Number(summary.reliability).toFixed(1)"
        unit="分"
        icon="Cpu"
        tone="gold"
        :hint="`${summary.task_count} 项任务 · 平均失效分 ${summary.avg_failure_score}`"
      />
    </div>

    <div class="grid-2">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">近六个月检测趋势</div>
          <div class="panel-note">按检测日期统计 · 双轴</div>
        </div>
        <div class="chart-body">
          <ChartPanel :option="trendOption" :height="300" :empty="!overview" />
        </div>
      </div>
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">样品类型合格率</div>
          <div class="panel-note">按检测记录汇总</div>
        </div>
        <div class="chart-body">
          <ChartPanel :option="typeRateOption" :height="300" :empty="!overview" />
        </div>
      </div>
    </div>

    <div class="grid-3">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">项目状态分布</div>
          <div class="panel-note">共 {{ summary.project_total }} 个项目</div>
        </div>
        <div class="chart-body">
          <ChartPanel :option="projectStatusOption" :height="252" :empty="!overview" />
        </div>
      </div>
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">样品类型构成</div>
          <div class="panel-note">共 {{ summary.sample_total }} 个样品</div>
        </div>
        <div class="chart-body">
          <ChartPanel :option="sampleTypeOption" :height="252" :empty="!overview" />
        </div>
      </div>
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">缺陷 TOP 分类</div>
          <div class="panel-note">{{ paretoNote }}</div>
        </div>
        <div class="chart-body">
          <ChartPanel :option="defectOption" :height="252" :empty="!overview" />
        </div>
      </div>
    </div>

    <div class="grid-2-even">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">最近检测记录</div>
          <router-link to="/test-records" class="panel-link">查看全部 →</router-link>
        </div>
        <div class="table-wrap">
          <el-table :data="overview?.recent_records || []" size="small">
            <el-table-column prop="sample_code" label="样品编号" width="112">
              <template #default="{ row }">
                <span class="mono">{{ row.sample_code }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="project_name" label="所属项目" min-width="150" show-overflow-tooltip />
            <el-table-column prop="item" label="检测项目" width="110" />
            <el-table-column label="实测 / 标准" width="116">
              <template #default="{ row }">
                <span class="num">{{ row.measured_value }}</span>
                <span class="muted"> / {{ row.standard_value }} {{ row.unit }}</span>
              </template>
            </el-table-column>
            <el-table-column label="结论" width="80">
              <template #default="{ row }">
                <StatusPill kind="conclusion" :value="row.conclusion" />
              </template>
            </el-table-column>
            <el-table-column label="检测时间" width="108">
              <template #default="{ row }">
                <span class="muted">{{ formatDate(row.tested_at) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">AI 协作快照</div>
          <router-link to="/ai-ops" class="panel-link">进入监管 →</router-link>
        </div>
        <div class="ai-snapshot">
          <div class="reliability-ring" :style="ringStyle">
            <div class="ring-inner">
              <strong class="num">{{ summary.reliability }}</strong>
              <span>综合可靠性</span>
            </div>
          </div>
          <div class="ai-facts">
            <div class="ai-fact">
              <span>高失效任务</span>
              <strong class="num text-fail">{{ summary.high_failure_count }} 项</strong>
            </div>
            <div class="ai-fact">
              <span>一次通过率</span>
              <strong class="num">{{ summary.success_rate }}%</strong>
            </div>
            <div class="ai-fact">
              <span>人工介入</span>
              <strong class="num">{{ aiStats?.summary?.human_minutes ?? 0 }} 分钟</strong>
            </div>
            <div class="ai-fact">
              <span>缺陷 AI 相关</span>
              <strong class="num">{{ aiStats?.summary?.ai_related_rate || 0 }}%</strong>
            </div>
          </div>
        </div>
        <div class="failure-list">
          <div class="failure-head">失效分 ≥ 40 的任务</div>
          <div
            v-for="task in (aiStats?.failure_cases || []).slice(0, 3)"
            :key="task.id"
            class="failure-item"
          >
            <div class="failure-main">
              <span class="failure-name">{{ task.task_name }}</span>
              <span class="failure-agent">{{ task.agent_name }} · {{ task.level }}</span>
            </div>
            <span class="score-chip" :class="{ danger: task.failure_score >= 60 }">
              FS {{ task.failure_score }}
            </span>
          </div>
          <div v-if="!(aiStats?.failure_cases || []).length" class="empty-cell">暂无高失效任务</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { aiApi, dashboardApi } from '@/api'
import ChartPanel from '@/components/ChartPanel.vue'
import StatCard from '@/components/StatCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import { auth } from '@/stores/auth'
import { AI_PHASE, CHART_COLORS, PROJECT_STATUS, SAMPLE_TYPE } from '@/constants/labels'

const router = useRouter()
const loading = ref(false)
const overview = ref(null)
const aiStats = ref(null)

const emptySummary = {
  project_total: 0,
  active_projects: 0,
  sample_total: 0,
  pending_samples: 0,
  test_total: 0,
  pass_total: 0,
  pass_rate: 0,
  open_defect_occurrences: 0,
  task_count: 0,
  avg_failure_score: 0,
  success_rate: 0,
  reliability: 0,
  high_failure_count: 0,
  human_minutes: 0
}

const summary = computed(() => ({ ...emptySummary, ...(overview.value?.summary || {}) }))
const todayLabel = dayjs().format('YYYY.MM.DD')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 11) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const ringStyle = computed(() => ({
  background: `conic-gradient(#d9a441 ${Math.max(0, Math.min(100, summary.value.reliability)) * 3.6}deg, #ece6d9 0deg)`
}))

const paretoNote = computed(() => {
  const pareto = overview.value?.defect_pareto || []
  if (!pareto.length) return '暂无缺陷数据'
  const top4 = pareto.slice(0, 4)
  return `前 ${top4.length} 类累计 ${top4[top4.length - 1].cumulative}%`
})

const chartBase = {
  textStyle: { fontFamily: 'Microsoft YaHei' },
  tooltip: {
    backgroundColor: 'rgba(12, 34, 56, .94)',
    borderWidth: 0,
    padding: [8, 12],
    textStyle: { color: '#fff', fontSize: 11 }
  }
}

const axisCommon = {
  axisLine: { lineStyle: { color: '#e5dfd2' } },
  axisTick: { show: false },
  axisLabel: { color: '#7c878d', fontSize: 10 },
  splitLine: { lineStyle: { color: '#f1ece1', type: 'dashed' } }
}

const trendOption = computed(() => {
  const rows = overview.value?.monthly_trend || []
  return {
    ...chartBase,
    grid: { left: 10, right: 14, top: 38, bottom: 6, containLabel: true },
    legend: {
      top: 4,
      right: 4,
      itemWidth: 10,
      itemHeight: 6,
      textStyle: { color: '#6c777e', fontSize: 10 }
    },
    tooltip: { ...chartBase.tooltip, trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: rows.map((item) => `${Number(item.month.slice(5))}月`),
      ...axisCommon,
      splitLine: { show: false }
    },
    yAxis: [
      {
        type: 'value',
        name: '记录数',
        nameTextStyle: { color: '#9aa2a4', fontSize: 10, padding: [0, 0, 0, -8] },
        ...axisCommon
      },
      {
        type: 'value',
        name: '合格率 %',
        min: 0,
        max: 100,
        nameTextStyle: { color: '#9aa2a4', fontSize: 10 },
        ...axisCommon,
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '合格',
        type: 'bar',
        stack: 'result',
        barWidth: 16,
        itemStyle: { color: '#2f6690', borderRadius: [3, 3, 0, 0] },
        data: rows.map((item) => item.pass)
      },
      {
        name: '不合格',
        type: 'bar',
        stack: 'result',
        itemStyle: { color: '#c06a3c', borderRadius: [3, 3, 0, 0] },
        data: rows.map((item) => item.fail)
      },
      {
        name: '合格率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#d9a441' },
        itemStyle: { color: '#d9a441', borderColor: '#fffdf8', borderWidth: 2 },
        data: rows.map((item) =>
          item.total ? Number(((item.pass / item.total) * 100).toFixed(1)) : null
        )
      }
    ]
  }
})

const typeRateOption = computed(() => {
  const rows = overview.value?.pass_rate_by_type || []
  return {
    ...chartBase,
    grid: { left: 8, right: 42, top: 16, bottom: 8, containLabel: true },
    tooltip: {
      ...chartBase.tooltip,
      trigger: 'item',
      formatter: (params) =>
        `${params.name}<br/>合格 ${params.data.pass} / ${params.data.total} 条<br/>合格率 ${params.value}%`
    },
    xAxis: {
      type: 'value',
      max: 100,
      ...axisCommon,
      axisLabel: { ...axisCommon.axisLabel, formatter: '{value}%' }
    },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.label),
      ...axisCommon,
      splitLine: { show: false }
    },
    series: [
      {
        type: 'bar',
        barWidth: 12,
        showBackground: true,
        backgroundStyle: { color: '#f2eee4', borderRadius: 6 },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: '#3d4b55',
          fontSize: 11,
          fontWeight: 600
        },
        data: rows.map((item) => ({
          value: item.rate,
          pass: item.pass,
          total: item.total,
          itemStyle: {
            borderRadius: 6,
            color:
              item.rate >= 90 ? '#2f7d5b' : item.rate >= 80 ? '#2f6690' : '#c06a3c'
          }
        }))
      }
    ]
  }
})

const projectStatusOption = computed(() => {
  const rows = overview.value?.project_status || []
  const colorMap = {
    PLANNING: '#a7a093',
    IN_PROGRESS: '#d9a441',
    ACCEPTED: '#2f7d5b',
    ARCHIVED: '#2f6690'
  }
  return {
    ...chartBase,
    tooltip: { ...chartBase.tooltip, trigger: 'item', formatter: '{b}<br/>{c} 个项目（{d}%）' },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#6c777e', fontSize: 10 }
    },
    series: [
      {
        type: 'pie',
        radius: ['48%', '70%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#fffdf8', borderWidth: 3 },
        label: { show: false },
        emphasis: { scale: true, scaleSize: 4 },
        data: rows.map((item) => ({
          name: PROJECT_STATUS[item.status]?.label || item.status,
          value: item.count,
          itemStyle: { color: colorMap[item.status] || '#a7a093' }
        }))
      }
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '34%',
        style: {
          text: String(summary.value.project_total),
          fill: '#0c2238',
          fontSize: 28,
          fontFamily: 'Bahnschrift',
          fontWeight: 600,
          textAlign: 'center'
        }
      },
      {
        type: 'text',
        left: 'center',
        top: '48%',
        style: {
          text: '项目',
          fill: '#8a9498',
          fontSize: 10,
          textAlign: 'center'
        }
      }
    ]
  }
})

const sampleTypeOption = computed(() => {
  const rows = overview.value?.sample_types || []
  return {
    ...chartBase,
    grid: { left: 8, right: 18, top: 16, bottom: 8, containLabel: true },
    tooltip: { ...chartBase.tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: rows.map((item) => (SAMPLE_TYPE[item.type]?.label || item.type).replace('试块', '').replace('样品', '')),
      ...axisCommon,
      splitLine: { show: false },
      axisLabel: { ...axisCommon.axisLabel, interval: 0 }
    },
    yAxis: { type: 'value', ...axisCommon, minInterval: 1 },
    series: [
      {
        type: 'bar',
        barWidth: 22,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (params) => CHART_COLORS[params.dataIndex % CHART_COLORS.length]
        },
        label: { show: true, position: 'top', color: '#4c5a63', fontSize: 11, fontWeight: 600 },
        data: rows.map((item) => item.count)
      }
    ]
  }
})

const defectOption = computed(() => {
  const rows = [...(overview.value?.defect_pareto || [])].slice(0, 5).reverse()
  return {
    ...chartBase,
    grid: { left: 8, right: 34, top: 10, bottom: 8, containLabel: true },
    tooltip: {
      ...chartBase.tooltip,
      trigger: 'item',
      formatter: (params) => `${params.name}<br/>${params.value} 次（${params.data.share}%）`
    },
    xAxis: { type: 'value', ...axisCommon },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.category),
      ...axisCommon,
      splitLine: { show: false }
    },
    series: [
      {
        type: 'bar',
        barWidth: 12,
        showBackground: true,
        backgroundStyle: { color: '#f2eee4', borderRadius: 6 },
        itemStyle: { color: '#c06a3c', borderRadius: 6 },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}',
          color: '#5f6a70',
          fontSize: 10,
          fontWeight: 600
        },
        data: rows.map((item) => ({ value: item.occurrences, share: item.share }))
      }
    ]
  }
})

function formatDate(value) {
  return value ? dayjs(value).format('MM-DD HH:mm') : '—'
}

async function loadAll() {
  loading.value = true
  try {
    const [overviewData, statsData] = await Promise.all([dashboardApi.overview(), aiApi.stats()])
    overview.value = overviewData
    aiStats.value = statsData
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.panel-link {
  font-size: 11px;
  color: var(--blue-500);
  letter-spacing: 0.04em;
}

.panel-link:hover {
  color: var(--accent);
}

.ai-snapshot {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 22px 22px 8px;
}

.reliability-ring {
  position: relative;
  width: 126px;
  height: 126px;
  flex: 0 0 126px;
  border-radius: 50%;
  display: grid;
  place-items: center;
}

.reliability-ring::after {
  content: "";
  position: absolute;
  inset: 9px;
  border-radius: 50%;
  background: #fffdf8;
  box-shadow: inset 0 0 0 1px #f0ebdf;
}

.ring-inner {
  position: relative;
  z-index: 1;
  text-align: center;
}

.ring-inner strong {
  display: block;
  font-size: 30px;
  line-height: 1;
  color: var(--navy-900);
}

.ring-inner span {
  display: block;
  margin-top: 6px;
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.06em;
}

.ai-facts {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px 18px;
}

.ai-fact {
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--line-soft);
}

.ai-fact span {
  display: block;
  font-size: 10.5px;
  color: var(--muted);
}

.ai-fact strong {
  display: block;
  margin-top: 5px;
  font-size: 16px;
  color: var(--navy-800);
}

.failure-list {
  padding: 4px 22px 18px;
}

.failure-head {
  padding: 10px 0 7px;
  font-size: 10.5px;
  letter-spacing: 0.1em;
  color: #8a9498;
  border-top: 1px dashed var(--line-soft);
}

.failure-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--line-soft);
}

.failure-item:last-child {
  border-bottom: none;
}

.failure-main {
  min-width: 0;
}

.failure-name {
  display: block;
  font-size: 12px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.failure-agent {
  display: block;
  margin-top: 3px;
  font-size: 10px;
  color: #919a9d;
}

.score-chip {
  flex: 0 0 auto;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: "Bahnschrift", sans-serif;
  font-size: 11px;
  color: #98631e;
  background: #fbf1dc;
  border: 1px solid #efdfbc;
}

.score-chip.danger {
  color: #a53d33;
  background: #f9e9e6;
  border-color: #eed3ce;
}
</style>
