<template>
  <span class="pill" :class="`pill--${config.tone}`">{{ config.label }}</span>
</template>

<script setup>
import { computed } from 'vue'
import {
  AI_LEVEL,
  AI_STATUS,
  CONCLUSION,
  DEFECT_STATUS,
  PROJECT_STATUS,
  ROLE,
  SAMPLE_STATUS,
  SAMPLE_TYPE,
  SEVERITY,
  lookup
} from '@/constants/labels'

const props = defineProps({
  kind: { type: String, required: true },
  value: { type: String, default: '' }
})

const maps = {
  project: PROJECT_STATUS,
  sampleType: SAMPLE_TYPE,
  sampleStatus: SAMPLE_STATUS,
  conclusion: CONCLUSION,
  aiLevel: AI_LEVEL,
  aiStatus: AI_STATUS,
  severity: SEVERITY,
  defectStatus: DEFECT_STATUS,
  role: ROLE
}

const config = computed(() => lookup(maps[props.kind] || {}, props.value))
</script>
