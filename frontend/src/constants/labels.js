export const PROJECT_STATUS = {
  PLANNING: { label: '筹备中', tone: 'gray' },
  IN_PROGRESS: { label: '进行中', tone: 'amber' },
  ACCEPTED: { label: '已验收', tone: 'green' },
  ARCHIVED: { label: '已归档', tone: 'blue' }
}

export const SAMPLE_TYPE = {
  CONCRETE: { label: '混凝土试块', tone: 'blue' },
  STEEL: { label: '钢筋', tone: 'amber' },
  SOIL: { label: '土工样品', tone: 'teal' },
  MORTAR: { label: '砂浆试块', tone: 'violet' },
  ASPHALT: { label: '沥青混合料', tone: 'gray' }
}

export const SAMPLE_STATUS = {
  PENDING: { label: '待检', tone: 'gray' },
  TESTING: { label: '检测中', tone: 'amber' },
  DONE: { label: '已完成', tone: 'green' }
}

export const CONCLUSION = {
  PASS: { label: '合格', tone: 'green' },
  FAIL: { label: '不合格', tone: 'red' }
}

export const AI_LEVEL = {
  L1: { label: 'L1 自动', tone: 'teal' },
  L2: { label: 'L2 协作', tone: 'amber' },
  L3: { label: 'L3 人工', tone: 'violet' }
}

export const AI_STATUS = {
  SUCCESS: { label: '成功', tone: 'green' },
  PARTIAL: { label: '部分可用', tone: 'amber' },
  FAILED: { label: '失败', tone: 'red' }
}

export const SEVERITY = {
  CRITICAL: { label: '致命', tone: 'red' },
  MAJOR: { label: '严重', tone: 'amber' },
  MINOR: { label: '一般', tone: 'blue' },
  TRIVIAL: { label: '轻微', tone: 'gray' }
}

export const DEFECT_STATUS = {
  OPEN: { label: '待修复', tone: 'red' },
  FIXED: { label: '已修复', tone: 'green' }
}

export const ROLE = {
  ADMIN: { label: '管理员', tone: 'violet' },
  ENGINEER: { label: '检测工程师', tone: 'blue' },
  VIEWER: { label: '查阅人员', tone: 'gray' }
}

export const AI_PHASE = {
  FEASIBILITY: '可行性分析',
  REQUIREMENTS: '需求分析',
  ARCHITECTURE: '总体设计',
  DETAILED_DESIGN: '详细设计',
  IMPLEMENTATION: '实现与测试',
  MAINTENANCE: '维护复盘'
}

export const RULE = {
  GTE: '实测值 ≥ 标准值',
  LTE: '实测值 ≤ 标准值'
}

export const CHART_COLORS = ['#1d4a6b', '#c06a3c', '#d9a441', '#2d6a73', '#7f8f99', '#8a5a44']

export function lookup(map, value) {
  return map[value] || { label: value || '—', tone: 'gray' }
}
