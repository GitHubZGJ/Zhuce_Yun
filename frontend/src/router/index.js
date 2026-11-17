import { createRouter, createWebHashHistory } from 'vue-router'
import { auth } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '数据看板' }
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('@/views/ProjectsView.vue'),
        meta: { title: '工程项目' }
      },
      {
        path: 'samples',
        name: 'samples',
        component: () => import('@/views/SamplesView.vue'),
        meta: { title: '检测样品' }
      },
      {
        path: 'test-records',
        name: 'test-records',
        component: () => import('@/views/TestRecordsView.vue'),
        meta: { title: '检测记录' }
      },
      {
        path: 'ai-ops',
        name: 'ai-ops',
        component: () => import('@/views/AiOpsView.vue'),
        meta: { title: 'AI 协作监管' }
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/UsersView.vue'),
        meta: { title: '用户管理', admin: true }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '工作台'} · 筑测云`
  if (to.meta.public) {
    if (auth.token && to.name === 'login') return { name: 'dashboard' }
    return true
  }
  if (!auth.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.admin && auth.user?.role !== 'ADMIN') {
    return { name: 'dashboard' }
  }
  return true
})

export default router
