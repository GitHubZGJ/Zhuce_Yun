<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-kicker">PROJECT REGISTRY</div>
        <h1 class="page-title">工程项目</h1>
        <p class="page-sub">维护检测合同所属的工程项目信息，样品与检测记录均挂接在项目之下。</p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="canEdit()" type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input
          v-model="query.q"
          placeholder="搜索项目编号 / 名称 / 建设单位"
          clearable
          style="width: 300px"
          :prefix-icon="Search"
          @keyup.enter="search"
          @clear="search"
        />
        <el-select v-model="query.status" placeholder="项目状态" clearable style="width: 150px" @change="search">
          <el-option
            v-for="(item, key) in PROJECT_STATUS"
            :key="key"
            :label="item.label"
            :value="key"
          />
        </el-select>
        <el-button @click="search">查询</el-button>
        <el-button text @click="reset">重置</el-button>
        <span class="grow"></span>
        <span class="dim-note">共 {{ total }} 个项目 · 当前第 {{ query.page }} 页</span>
      </div>

      <div class="table-wrap">
        <el-table :data="rows" v-loading="loading" row-key="id">
          <el-table-column label="项目编号" width="132">
            <template #default="{ row }">
              <span class="mono">{{ row.code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="项目名称" min-width="190" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="strong">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="client" label="建设单位" min-width="150" show-overflow-tooltip />
          <el-table-column prop="manager" label="项目负责人" width="106" />
          <el-table-column label="工期" width="190">
            <template #default="{ row }">
              <span class="muted">{{ row.start_date || '—' }} 至 {{ row.end_date || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <StatusPill kind="project" :value="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="样品" width="76" align="center">
            <template #default="{ row }">
              <span class="num">{{ row.sample_count }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
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
      :title="dialog.mode === 'create' ? '新建工程项目' : '编辑工程项目'"
      width="640px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <div class="form-grid">
          <el-form-item label="项目编号" prop="code">
            <el-input v-model="form.code" placeholder="如 XM-2026-008" maxlength="40" />
          </el-form-item>
          <el-form-item label="项目名称" prop="name">
            <el-input v-model="form.name" placeholder="工程全称" maxlength="120" />
          </el-form-item>
          <el-form-item label="建设单位" prop="client">
            <el-input v-model="form.client" maxlength="120" />
          </el-form-item>
          <el-form-item label="项目地点" prop="location">
            <el-input v-model="form.location" maxlength="120" />
          </el-form-item>
          <el-form-item label="负责人" prop="manager">
            <el-input v-model="form.manager" maxlength="50" />
          </el-form-item>
          <el-form-item label="项目状态" prop="status">
            <el-select v-model="form.status" style="width: 100%">
              <el-option
                v-for="(item, key) in PROJECT_STATUS"
                :key="key"
                :label="item.label"
                :value="key"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="开始日期" prop="start_date">
            <el-date-picker
              v-model="form.start_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="结束日期" prop="end_date">
            <el-date-picker
              v-model="form.end_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="项目说明" class="span-2">
            <el-input v-model="form.description" type="textarea" :rows="3" maxlength="1000" show-word-limit />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="dialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存项目</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { projectApi } from '@/api'
import StatusPill from '@/components/StatusPill.vue'
import { PROJECT_STATUS } from '@/constants/labels'
import { canEdit, isAdmin } from '@/stores/auth'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const formRef = ref()

const query = reactive({ page: 1, page_size: 10, q: '', status: '' })

const emptyForm = () => ({
  id: null,
  code: '',
  name: '',
  client: '',
  location: '',
  manager: '',
  status: 'PLANNING',
  start_date: '',
  end_date: '',
  description: ''
})

const form = reactive(emptyForm())
const dialog = reactive({ visible: false, mode: 'create' })

const rules = {
  code: [{ required: true, message: '请输入项目编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  client: [{ required: true, message: '请输入建设单位', trigger: 'blur' }],
  location: [{ required: true, message: '请输入项目地点', trigger: 'blur' }],
  manager: [{ required: true, message: '请输入项目负责人', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    const data = await projectApi.list({
      page: query.page,
      page_size: query.page_size,
      q: query.q || undefined,
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

function search() {
  query.page = 1
  load()
}

function reset() {
  query.q = ''
  query.status = ''
  query.page = 1
  load()
}

function openCreate() {
  Object.assign(form, emptyForm())
  dialog.mode = 'create'
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, {
    ...emptyForm(),
    ...row,
    start_date: row.start_date || '',
    end_date: row.end_date || ''
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
      code: form.code,
      name: form.name,
      client: form.client,
      location: form.location,
      manager: form.manager,
      status: form.status,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      description: form.description || ''
    }
    if (dialog.mode === 'create') {
      await projectApi.create(payload)
      ElMessage.success('项目创建成功')
    } else {
      await projectApi.update(form.id, payload)
      ElMessage.success('项目已更新')
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
      `确认删除项目「${row.name}」？项目下存在样品时系统会拒绝删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await projectApi.remove(row.id)
    ElMessage.success('项目已删除')
    if (rows.value.length === 1 && query.page > 1) query.page -= 1
    load()
  } catch {
    /* 已统一提示 */
  }
}

onMounted(load)
</script>
