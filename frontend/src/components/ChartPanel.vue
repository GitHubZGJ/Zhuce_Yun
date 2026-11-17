<template>
  <div class="chart-shell">
    <div ref="chartEl" class="chart-canvas" :style="{ height: `${height}px` }"></div>
    <div v-if="empty" class="chart-empty" :style="{ height: `${height}px` }">
      <el-icon><DataLine /></el-icon>
      <span>{{ emptyText }}</span>
    </div>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  height: { type: Number, default: 300 },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无可展示的数据' }
})

const chartEl = ref(null)
let chart = null
let observer = null

function render() {
  if (!chartEl.value || props.empty) return
  if (!chart) {
    chart = echarts.init(chartEl.value)
  }
  chart.setOption(props.option, true)
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  render()
  observer = new ResizeObserver(resize)
  if (chartEl.value) observer.observe(chartEl.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})

watch(
  () => props.option,
  () => render(),
  { deep: true }
)

watch(
  () => props.empty,
  async (value) => {
    if (value) {
      chart?.clear()
      return
    }
    await nextTick()
    render()
    resize()
  }
)
</script>

<style scoped>
.chart-shell {
  position: relative;
  width: 100%;
}

.chart-canvas {
  width: 100%;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #8a8f8c;
  font-size: 12px;
  background: linear-gradient(180deg, rgba(248, 244, 236, 0.4), transparent);
}

.chart-empty .el-icon {
  font-size: 26px;
  opacity: 0.55;
}
</style>
