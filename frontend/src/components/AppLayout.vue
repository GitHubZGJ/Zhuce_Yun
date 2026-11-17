<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div class="brand-text">
          <div class="brand-title">筑测云</div>
          <div class="brand-sub">Zhuce Cloud · QC</div>
        </div>
      </div>

      <div class="nav-section">业务工作台</div>
      <router-link to="/dashboard" class="nav-item" active-class="active">
        <el-icon><Odometer /></el-icon><span class="nav-label">数据看板</span>
      </router-link>
      <router-link to="/projects" class="nav-item" active-class="active">
        <el-icon><OfficeBuilding /></el-icon><span class="nav-label">工程项目</span>
      </router-link>
      <router-link to="/samples" class="nav-item" active-class="active">
        <el-icon><CollectionTag /></el-icon><span class="nav-label">检测样品</span>
      </router-link>
      <router-link to="/test-records" class="nav-item" active-class="active">
        <el-icon><DataAnalysis /></el-icon><span class="nav-label">检测记录</span>
      </router-link>

      <div class="nav-section">质量与协作</div>
      <router-link to="/ai-ops" class="nav-item" active-class="active">
        <el-icon><Cpu /></el-icon><span class="nav-label">AI 协作监管</span>
      </router-link>

      <template v-if="isAdmin()">
        <div class="nav-section">系统设置</div>
        <router-link to="/users" class="nav-item" active-class="active">
          <el-icon><UserFilled /></el-icon><span class="nav-label">用户管理</span>
        </router-link>
      </template>

      <div class="sidebar-foot">
        <strong>Agent 协作可靠性</strong>
        <div class="sidebar-gauge"><span :style="{ width: `${reliability}%` }"></span></div>
        <div>{{ stats.task_count }} 项任务 · 综合 {{ reliability }} 分</div>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div class="topbar-left">
          <span>筑测云</span>
          <span class="topbar-divider"></span>
          <span class="topbar-page">{{ route.meta.title || '工作台' }}</span>
        </div>
        <div class="topbar-right">
          <span class="topbar-date">{{ today }}</span>
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-trigger">
              <div class="avatar">{{ initial }}</div>
              <div>
                <div class="user-name">{{ auth.user?.display_name || '未登录' }}</div>
                <div class="user-role">{{ roleLabel(auth.user?.role) }}</div>
              </div>
              <el-icon style="color: #7a8a95; font-size: 12px"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  {{ auth.user?.username }} · {{ roleLabel(auth.user?.role) }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aiApi, authApi } from '@/api'
import { auth, clearAuth, isAdmin, roleLabel } from '@/stores/auth'

dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()

const stats = reactive({ task_count: 0, reliability: 0 })

const today = computed(() => dayjs().format('YYYY年M月D日 dddd'))
const initial = computed(() => (auth.user?.display_name || '筑').slice(0, 1))

onMounted(async () => {
  try {
    const data = await aiApi.stats()
    stats.task_count = data.summary.task_count
    stats.reliability = data.summary.reliability
  } catch {
    /* 顶部辅助信息失败不打断主流程 */
  }
})

async function handleCommand(command) {
  if (command !== 'logout') return
  try {
    await authApi.logout()
  } catch {
    /* 无状态 JWT，退出失败也清理本地令牌 */
  }
  clearAuth()
  ElMessage.success('已安全退出')
  router.push('/login')
}
</script>

<style scoped>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.16s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
