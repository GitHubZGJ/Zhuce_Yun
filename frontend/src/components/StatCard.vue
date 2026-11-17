<template>
  <div class="stat-card" :class="tone">
    <div class="stat-top">
      <div>
        <div class="stat-label">{{ label }}</div>
        <div class="stat-value">
          {{ value }}<span v-if="unit" class="stat-unit">{{ unit }}</span>
        </div>
      </div>
      <div class="stat-icon">
        <el-icon><component :is="icon" /></el-icon>
      </div>
    </div>
    <div class="stat-foot">
      <slot>
        <span>{{ hint }}</span>
      </slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  hint: { type: String, default: '' },
  tone: { type: String, default: '' },
  icon: { type: String, default: 'DataLine' }
})
</script>
