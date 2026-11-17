<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-kicker">TEST RECORDS</div>
        <h1 class="page-title">检测记录</h1>
        <p class="page-sub">录入实测值后由系统按 GTE / LTE 规则自动判定，并同步样品状态与看板指标。</p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="canEdit()" type="primary" :icon="Plus" @click="openCreate">录入检测</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input
          v-model="query.q"
          placeholder="搜索样品编号 / 检测项目 / 项目"
          clearable
          style="width: 280px"
          :prefix-icon="Search"
          @keyup.enter="search"
          @clear="search"
        />
        <el-select v-model="query.project_id" placeholder="所属项目" clearable filterable style="width: 210px" @change="search">
          <el-option
            v-for="item in projectOptions"
            :key="item.id"
            :label="`${item.code} · ${item.name}`"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="query.conclusion" placeholder="判定结论" clearable style="width: 120px" @change="search">
          <el-option label="合格" value="PASS" />
          <el-option label="不合格" value="FAIL" />
        </el-select>
        <el-date-picker
          v-model="query.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="检测开始"
          end-placeholder="检测结束"
          style="width: 240px"
          @change="search"
        />
        <el-button @click="search">查询</el-button>
        <el-button text @click="reset">重置</el-button>
        <span class="grow"></span>
        <span class="dim-note">共 {{ total }} 条记录</span>
      </div>

      <div class="table-wrap">
        <el-table :data="rows" v-loading="loading" row-key="id">
          <el-table-column label="样品编号" width="108">
            <template #default="{ row }"><span class="mono">{{ row.sample_code }}</span></template>
          </el-table-column>
          <el-table-column prop="project_name" label="所属项目" min-width="150" show-overflow-tooltip />
          <el-table-column label="类型" width="104">
            <template #default="{ row }"><StatusPill kind="sampleType" :value="row.sample_type" /></template>
          </el-table-column>
          <el-table-column prop="item" label="检测项目" min-width="130" show-overflow-tooltip />
          <el-table-column label="标准值" width="94" align="right">
            <template #default="{ row }">
              <span class="num">{{ row.standard_value }}</span>
              <span class="muted"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实测值" width="94" align="right">
            <template #default="{ row }">
              <span class="num" :class="row.conclusion === 'FAIL' ? 'text-fail' : ''">{{ row.measured_value }}</span>
              <span class="muted"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="判定" width="82">
            <template #default="{ row }">
              <StatusPill kind="conclusion" :value="row.conclusion" />
            </template>
          </el-table-column>
          <el-table-column prop="tester_name" label="检测人" width="82" />
          <el-table-column label="检测时间" width="116">
            <template #default="{ row }"><span class="muted">{{ formatTime(row.tested_at) }}</span></template>
          </el-table-column>
          <el-table-column label="操作" width="118" fixed="right">
            <template #default="{ row }">
              <template v-if="canEdit()">
                <el-button link type="primary" @click="openEdit(row)">修正</el-button>
                <el-button v-if="isAdmin()" link type="danger" @click="remove(row)">删除</el-button>
              </template>
              <span v-else class="muted">只读</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="search"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialog.visible"
      :title="dialog.mode === 'create' ? '录入检测记录' : '修正检测记录'"
      width="720px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <div class="form-grid">
          <el-form-item label="检测样品" prop="sample_id" class="span-2">
            <el-select
              v-model="form.sample_id"
              filterable
              placeholder="按样品编号 / 项目搜索"
              style="width: 100%"
              :disabled="dialog.mode === 'edit'"
            >
              <el-option
                v-for="item in sampleOptions"
                :key="item.id"
                :label="`${item.code} · ${item.project_name} · ${SAMPLE_TYPE[item.type]?.label || item.type}`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="检测项目" prop="item">
            <el-input v-model="form.item" placeholder="如 抗压强度（28d）" maxlength="60" />
          </el-form-item>
          <el-form-item label="计量单位" prop="unit">
            <el-input v-model="form.unit" placeholder="MPa / % / kN" maxlength="20" />
          </el-form-item>
          <el-form-item label="标准值" prop="standard_value">
            <el-input-number
              v-model="form.standard_value"
              :min="0.01"
              :precision="2"
              :controls="false"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="实测值" prop="measured_value">
            <el-input-number
              v-model="form.measured_value"
              :min="0.01"
              :precision="2"
              :controls="false"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="判定规则" prop="rule">
            <el-select v-model="form.rule" style="width: 100%">
              <el-option label="实测值 ≥ 标准值（GTE）" value="GTE" />
              <el-option label="实测值 ≤ 标准值（LTE）" value="LTE" />
            </el-select>
          </el-form-item>
          <el-form-item label="检测时间" prop="tested_at">
            <el-date-picker
              v-model="form.tested_at"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              placeholder="选择检测时间"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="备注" class="span-2">
            <el-input v-model="form.remark" placeholder="依据标准、复检说明等" maxlength="255" />
          </el-form-item>
        </div>

        <div class="judge-preview" :class="previewTone">
          <div class="judge-icon">
            <el-icon v-if="preview === 'PASS'"><CircleCheck /></el-icon>
            <el-icon v-else-if="preview === 'FAIL'"><CircleClose /></el-icon>
            <el-icon v-else><QuestionFilled /></el-icon>
          </div>
          <div>
            <strong>{{ previewText }}</strong>
            <p>
              规则：{{ RULE[form.rule] }}；比较前统一保留两位小数，避免浮点边界误差。
            </p>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="dialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">
            {{ dialog.mode === 'create' ? '保存并判定' : '保存修正' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, CircleClose, Plus, QuestionFilled, Refresh, Search } from '@element-plus/icons-vue'
import { projectApi, recordApi, sampleApi } from '@/api'
import StatusPill from '@/components/StatusPill.vue'
import { RULE, SAMPLE_TYPE } from '@/constants/labels'
import { canEdit, isAdmin } from '@/stores/auth'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const projectOptions = ref([])
const sampleOptions = ref([])
const formRef = ref()

const query = reactive({
  page: 1,
  page_size: 10,
  q: '',
  project_id: null,
  conclusion: '',
  dateRange: []
})

const emptyForm = () => ({
  id: null,
  sample_id: null,
  item: '',
  unit: 'MPa',
  standard_value: null,
  measured_value: null,
  rule: 'GTE',
  tested_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
  remark: ''
})

const form = reactive(emptyForm())
const dialog = reactive({ visible: false, mode: 'create' })

const rules = {
  sample_id: [{ required: true, message: '请选择检测样品', trigger: 'change' }],
  item: [{ required: true, message: '请输入检测项目', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入计量单位', trigger: 'blur' }],
  standard_value: [{ required: true, message: '请输入标准值', trigger: 'blur' }],
  measured_value: [{ required: true, message: '请输入实测值', trigger: 'blur' }],
  rule: [{ required: true, message: '请选择判定规则', trigger: 'change' }]
}

const preview = computed(() => {
  if (form.standard_value == null || form.measured_value == null) return ''
  const standard = Math.round(Number(form.standard_value) * 100) / 100
  const measured = Math.round(Number(form.measured_value) * 100) / 100
  if (!Number.isFinite(standard) || !Number.isFinite(measured)) return ''
  return form.rule === 'GTE'
    ? measured >= standard
      ? 'PASS'
      : 'FAIL'
    : measured <= standard
      ? 'PASS'
      : 'FAIL'
})

const previewTone = computed(() => {
  if (preview.value === 'PASS') return 'is-pass'
  if (preview.value === 'FAIL') return 'is-fail'
  return 'is-idle'
})

const previewText = computed(() => {
  if (preview.value === 'PASS') return '预计判定：合格'
  if (preview.value === 'FAIL') return '预计判定：不合格'
  return '填写标准值与实测值后自动预览判定'
})

function formatTime(value) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '—'
}

async function load() {
  loading.value = true
  try {
    const [start, end] = query.dateRange || []
    const data = await recordApi.list({
      page: query.page,
      page_size: query.page_size,
      q: query.q || undefined,
      project_id: query.project_id || undefined,
      conclusion: query.conclusion || undefined,
      start_date: start || undefined,
      end_date: end || undefined
    })
    rows.value = data.items
    total.value = data.total
  } catch {
    /* 已统一提示 */
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [projects, samples] = await Promise.all([
      projectApi.options(),
      sampleApi.list({ page: 1, page_size: 100 })
    ])
    projectOptions.value = projects
    sampleOptions.value = samples.items
  } catch {
    projectOptions.value = []
    sampleOptions.value = []
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, { page: 1, q: '', project_id: null, conclusion: '', dateRange: [] })
  load()
}

function openCreate() {
  Object.assign(form, emptyForm())
  dialog.mode = 'create'
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    sample_id: row.sample_id,
    item: row.item,
    unit: row.unit,
    standard_value: row.standard_value,
    measured_value: row.measured_value,
    rule: row.rule,
    tested_at: row.tested_at ? dayjs(row.tested_at).format('YYYY-MM-DDTHH:mm:ss') : '',
    remark: row.remark || ''
  })
  dialog.mode = 'edit'
  dialog.visible = true
}

async function save() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload = {
      sample_id: form.sample_id,
      item: form.item,
      unit: form.unit,
      standard_value: form.standard_value,
      measured_value: form.measured_value,
      rule: form.rule,
      tested_at: form.tested_at || null,
      remark: form.remark || ''
    }
    if (dialog.mode === 'create') {
      const data = await recordApi.create(payload)
      ElMessage.success(`检测记录已保存，判定结果：${data.conclusion === 'PASS' ? '合格' : '不合格'}`)
    } else {
      await recordApi.update(form.id, payload)
      ElMessage.success('检测记录已修正并重新判定')
    }
    dialog.visible = false
    loadOptions()
    load()
  } catch {
    /* 已统一提示 */
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除样品 ${row.sample_code} 的「${row.item}」检测记录？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await recordApi.remove(row.id)
    ElMessage.success('检测记录已删除')
    if (rows.value.length === 1 && query.page > 1) query.page -= 1
    load()
  } catch {
    /* 已统一提示 */
  }
}

onMounted(() => {
  loadOptions()
  load()
})
</script>

<style scoped>
.judge-preview {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin: 4px 0 8px;
  padding: 13px 15px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #faf7ef;
}

.judge-icon {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 17px;
  background: rgba(29, 74, 107, 0.08);
  color: var(--blue-500);
}

.judge-preview strong {
  display: block;
  font-size: 13px;
  color: var(--navy-800);
}

.judge-preview p {
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.6;
  color: var(--muted);
}

.judge-preview.is-pass {
  border-color: #cfe5d9;
  background: #f0f7f2;
}

.judge-preview.is-pass .judge-icon {
  color: var(--pass);
  background: #e1f0e7;
}

.judge-preview.is-fail {
  border-color: #eed3ce;
  background: #fbf1ef;
}

.judge-preview.is-fail .judge-icon {
  color: var(--fail);
  background: #f6e2de;
}
</style>
