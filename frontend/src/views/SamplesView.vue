<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-kicker">SAMPLE LEDGER</div>
        <h1 class="page-title">检测样品</h1>
        <p class="page-sub">登记进入检测流程的试块、钢筋、土工与沥青样品，样品是检测记录的归属单元。</p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="canEdit()" type="primary" :icon="Plus" @click="openCreate">登记样品</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input
          v-model="query.q"
          placeholder="搜索样品编号 / 规格 / 项目"
          clearable
          style="width: 270px"
          :prefix-icon="Search"
          @keyup.enter="search"
          @clear="search"
        />
        <el-select v-model="query.project_id" placeholder="所属项目" clearable filterable style="width: 220px" @change="search">
          <el-option
            v-for="item in projectOptions"
            :key="item.id"
            :label="`${item.code} · ${item.name}`"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="query.type" placeholder="样品类型" clearable style="width: 130px" @change="search">
          <el-option v-for="(item, key) in SAMPLE_TYPE" :key="key" :label="item.label" :value="key" />
        </el-select>
        <el-select v-model="query.status" placeholder="样品状态" clearable style="width: 120px" @change="search">
          <el-option v-for="(item, key) in SAMPLE_STATUS" :key="key" :label="item.label" :value="key" />
        </el-select>
        <el-button @click="search">查询</el-button>
        <el-button text @click="reset">重置</el-button>
        <span class="grow"></span>
        <span class="dim-note">共 {{ total }} 个样品</span>
      </div>

      <div class="table-wrap">
        <el-table :data="rows" v-loading="loading" row-key="id">
          <el-table-column label="样品编号" width="112">
            <template #default="{ row }"><span class="mono">{{ row.code }}</span></template>
          </el-table-column>
          <el-table-column prop="project_name" label="所属项目" min-width="170" show-overflow-tooltip />
          <el-table-column label="类型" width="112">
            <template #default="{ row }">
              <StatusPill kind="sampleType" :value="row.type" />
            </template>
          </el-table-column>
          <el-table-column prop="spec" label="规格 / 说明" min-width="170" show-overflow-tooltip />
          <el-table-column label="生产日期" width="102">
            <template #default="{ row }">
              <span class="muted">{{ row.produced_on || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="62" align="center">
            <template #default="{ row }"><span class="num">{{ row.quantity }}</span></template>
          </el-table-column>
          <el-table-column label="状态" width="88">
            <template #default="{ row }">
              <StatusPill kind="sampleStatus" :value="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="检测记录" width="80" align="center">
            <template #default="{ row }"><span class="num">{{ row.test_count }}</span></template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <template v-if="canEdit()">
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
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
      :title="dialog.mode === 'create' ? '登记检测样品' : '编辑检测样品'"
      width="600px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <div class="form-grid">
          <el-form-item label="样品编号" prop="code">
            <el-input v-model="form.code" placeholder="如 YP-260901" maxlength="40" />
          </el-form-item>
          <el-form-item label="所属项目" prop="project_id">
            <el-select v-model="form.project_id" filterable placeholder="选择项目" style="width: 100%">
              <el-option
                v-for="item in projectOptions"
                :key="item.id"
                :label="`${item.code} · ${item.name}`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="样品类型" prop="type">
            <el-select v-model="form.type" style="width: 100%">
              <el-option v-for="(item, key) in SAMPLE_TYPE" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="样品状态" prop="status">
            <el-select v-model="form.status" style="width: 100%">
              <el-option v-for="(item, key) in SAMPLE_STATUS" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="规格说明" prop="spec" class="span-2">
            <el-input v-model="form.spec" placeholder="如 C30 150×150×150mm / HRB400E Φ20" maxlength="80" />
          </el-form-item>
          <el-form-item label="生产日期" prop="produced_on">
            <el-date-picker
              v-model="form.produced_on"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="数量" prop="quantity">
            <el-input-number v-model="form.quantity" :min="1" :max="1000" style="width: 100%" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="dialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存样品</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { projectApi, sampleApi } from '@/api'
import StatusPill from '@/components/StatusPill.vue'
import { SAMPLE_STATUS, SAMPLE_TYPE } from '@/constants/labels'
import { canEdit, isAdmin } from '@/stores/auth'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const projectOptions = ref([])
const formRef = ref()

const query = reactive({
  page: 1,
  page_size: 10,
  q: '',
  project_id: null,
  type: '',
  status: ''
})

const emptyForm = () => ({
  id: null,
  code: '',
  project_id: null,
  type: 'CONCRETE',
  spec: '',
  produced_on: '',
  quantity: 3,
  status: 'PENDING'
})

const form = reactive(emptyForm())
const dialog = reactive({ visible: false, mode: 'create' })

const rules = {
  code: [{ required: true, message: '请输入样品编号', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  type: [{ required: true, message: '请选择样品类型', trigger: 'change' }],
  spec: [{ required: true, message: '请输入规格说明', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    const data = await sampleApi.list({
      page: query.page,
      page_size: query.page_size,
      q: query.q || undefined,
      project_id: query.project_id || undefined,
      type: query.type || undefined,
      status: query.status || undefined
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
    projectOptions.value = await projectApi.options()
  } catch {
    projectOptions.value = []
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, { page: 1, q: '', project_id: null, type: '', status: '' })
  load()
}

function openCreate() {
  Object.assign(form, emptyForm())
  dialog.mode = 'create'
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, { ...emptyForm(), ...row, produced_on: row.produced_on || '' })
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
      code: form.code,
      project_id: form.project_id,
      type: form.type,
      spec: form.spec,
      produced_on: form.produced_on || null,
      quantity: form.quantity,
      status: form.status
    }
    if (dialog.mode === 'create') {
      await sampleApi.create(payload)
      ElMessage.success('样品登记成功')
    } else {
      await sampleApi.update(form.id, payload)
      ElMessage.success('样品已更新')
    }
    dialog.visible = false
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
      `确认删除样品「${row.code}」？样品下存在检测记录时系统会拒绝删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await sampleApi.remove(row.id)
    ElMessage.success('样品已删除')
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
