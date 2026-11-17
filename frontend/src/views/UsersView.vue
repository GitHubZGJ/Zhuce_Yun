<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-kicker">ACCESS CONTROL</div>
        <h1 class="page-title">用户管理</h1>
        <p class="page-sub">管理员维护账号、角色与启停状态。系统采用 JWT + RBAC，角色分为管理员、检测工程师与查阅人员。</p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input
          v-model="query.q"
          placeholder="搜索登录名 / 显示名"
          clearable
          style="width: 260px"
          :prefix-icon="Search"
          @keyup.enter="search"
          @clear="search"
        />
        <el-button @click="search">查询</el-button>
        <el-button text @click="reset">重置</el-button>
        <span class="grow"></span>
        <span class="dim-note">共 {{ total }} 个账号</span>
      </div>

      <div class="table-wrap">
        <el-table :data="rows" v-loading="loading" row-key="id">
          <el-table-column label="登录名" width="140">
            <template #default="{ row }"><span class="mono">{{ row.username }}</span></template>
          </el-table-column>
          <el-table-column prop="display_name" label="显示名" min-width="120">
            <template #default="{ row }"><span class="strong">{{ row.display_name }}</span></template>
          </el-table-column>
          <el-table-column label="角色" width="122">
            <template #default="{ row }"><StatusPill kind="role" :value="row.role" /></template>
          </el-table-column>
          <el-table-column label="状态" width="94">
            <template #default="{ row }">
              <span class="pill" :class="row.is_active ? 'pill--green' : 'pill--gray'">
                {{ row.is_active ? '启用' : '停用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="最近登录" min-width="150">
            <template #default="{ row }">
              <span class="muted">{{ row.last_login_at ? formatTime(row.last_login_at) : '尚未登录' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="140">
            <template #default="{ row }">
              <span class="muted">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="96" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
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
      :title="dialog.mode === 'create' ? '新增用户' : '编辑用户'"
      width="520px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="登录名" prop="username">
          <el-input v-model="form.username" :disabled="dialog.mode === 'edit'" maxlength="50" />
        </el-form-item>
        <el-form-item label="显示名" prop="display_name">
          <el-input v-model="form.display_name" maxlength="50" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="检测工程师" value="ENGINEER" />
            <el-option label="查阅人员" value="VIEWER" />
          </el-select>
        </el-form-item>
        <el-form-item :label="dialog.mode === 'create' ? '初始密码' : '重置密码'" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="dialog.mode === 'edit' ? '留空表示不修改' : '至少 6 位'"
            maxlength="64"
          />
        </el-form-item>
        <el-form-item v-if="dialog.mode === 'edit'" label="账号状态">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="停用"
            :disabled="form.id === auth.user?.id"
          />
          <div v-if="form.id === auth.user?.id" class="self-note">当前登录账号不可停用或降级。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="dialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import StatusPill from '@/components/StatusPill.vue'
import { auth } from '@/stores/auth'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const formRef = ref()

const query = reactive({ page: 1, page_size: 10, q: '' })
const form = reactive({
  id: null,
  username: '',
  display_name: '',
  role: 'ENGINEER',
  password: '',
  is_active: true
})
const dialog = reactive({ visible: false, mode: 'create' })

const rules = {
  username: [
    { required: true, message: '请输入登录名', trigger: 'blur' },
    { min: 3, max: 50, message: '登录名长度为 3–50 位', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_.-]+$/, message: '仅允许字母、数字、下划线、点与短横线', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名', trigger: 'blur' },
    { min: 2, max: 50, message: '显示名长度为 2–50 位', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [
    {
      validator: (rule, value, callback) => {
        if (dialog.mode === 'create' && !value) {
          callback(new Error('请输入初始密码'))
          return
        }
        if (value && (value.length < 6 || value.length > 64)) {
          callback(new Error('密码长度为 6–64 位'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

function formatTime(value) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '—'
}

async function load() {
  loading.value = true
  try {
    const data = await userApi.list({
      page: query.page,
      page_size: query.page_size,
      q: query.q || undefined
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
  query.page = 1
  load()
}

function openCreate() {
  Object.assign(form, {
    id: null,
    username: '',
    display_name: '',
    role: 'ENGINEER',
    password: '',
    is_active: true
  })
  dialog.mode = 'create'
  dialog.visible = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    username: row.username,
    display_name: row.display_name,
    role: row.role,
    password: '',
    is_active: row.is_active
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
    if (dialog.mode === 'create') {
      await userApi.create({
        username: form.username,
        display_name: form.display_name,
        role: form.role,
        password: form.password
      })
      ElMessage.success('用户创建成功')
    } else {
      const payload = {
        display_name: form.display_name,
        role: form.role,
        is_active: form.is_active
      }
      if (form.password) payload.password = form.password
      await userApi.update(form.id, payload)
      ElMessage.success('用户信息已更新')
    }
    dialog.visible = false
    load()
  } catch {
    /* 已统一提示 */
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.self-note {
  margin-top: 5px;
  font-size: 10.5px;
  color: var(--warn);
}
</style>
