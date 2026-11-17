<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="blueprint-grid"></div>
      <div class="brand-top">
        <div class="brand-mark"></div>
        <div>
          <div class="brand-title">筑测云</div>
          <div class="brand-sub">ZHUCE CLOUD · ENGINEERING QC</div>
        </div>
      </div>

      <div class="brand-main">
        <div class="kicker">GENERATIVE SOFTWARE ENGINEERING · 2026</div>
        <h1>工程有据<br /><span>检测有数</span></h1>
        <p class="brand-desc">
          面向施工项目部与检测机构的一体化工作台。从项目登记到检测判定，
          再到 AI 协作可靠性监管，让每一份数据都留下可追溯的工程依据。
        </p>

        <div class="feature-list">
          <div class="feature">
            <span class="feature-index">01</span>
            <div>
              <strong>项目 · 样品 · 检测闭环</strong>
              <p>工程项目、检测样品与检测记录全链路管理，结果自动判定。</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-index">02</span>
            <div>
              <strong>看板驱动质量决策</strong>
              <p>合格率、样品分布与月度趋势实时汇总，异常一眼可见。</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-index">03</span>
            <div>
              <strong>Agent 失效评分与分级</strong>
              <p>L1/L2/L3 协作分级，失效分量化 AI 可靠性，纳入维护复盘。</p>
            </div>
          </div>
        </div>
      </div>

      <div class="brand-foot">
        <div class="brand-metric"><strong class="num">6</strong><span>在建工程</span></div>
        <div class="brand-metric"><strong class="num">60</strong><span>检测记录</span></div>
        <div class="brand-metric"><strong class="num">24</strong><span>AI 任务</span></div>
        <div class="brand-metric"><strong class="num">85.3</strong><span>协作可靠性</span></div>
      </div>

      <div class="beam-art" aria-hidden="true">
        <svg viewBox="0 0 460 260" fill="none">
          <path d="M20 190 L180 80 L340 190 L440 120" stroke="rgba(217,164,65,.42)" stroke-width="1.2" />
          <path d="M20 190 L180 80 L340 190" stroke="rgba(255,255,255,.16)" stroke-width="1" />
          <path d="M180 80 L180 210 M20 190 L180 210 L340 190" stroke="rgba(255,255,255,.09)" stroke-dasharray="4 6" />
          <circle cx="180" cy="80" r="4" fill="#d9a441" />
          <circle cx="20" cy="190" r="3" fill="rgba(255,255,255,.4)" />
          <circle cx="340" cy="190" r="3" fill="rgba(255,255,255,.4)" />
          <path d="M46 178 L96 143" stroke="rgba(217,164,65,.5)" stroke-width="1" />
          <path d="M52 186 L102 151" stroke="rgba(217,164,65,.24)" stroke-width="1" />
          <text x="28" y="232" fill="rgba(203,218,229,.42)" font-size="10" letter-spacing="3">STRUCTURE / DATA / TRACEABILITY</text>
        </svg>
      </div>
    </section>

    <section class="login-panel">
      <div class="form-wrap">
        <div class="form-head">
          <div class="form-mark">筑</div>
          <div>
            <h2>登录工作台</h2>
            <p>项目检测与 AI 协作监管统一入口</p>
          </div>
        </div>

        <el-form :model="form" label-position="top" @submit.prevent="submit">
          <el-form-item label="账号">
            <el-input
              v-model="form.username"
              size="large"
              placeholder="请输入登录名"
              autocomplete="username"
              :prefix-icon="User"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              placeholder="请输入密码"
              autocomplete="current-password"
              :prefix-icon="Lock"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="submit"
          >
            进入工作台
          </el-button>
        </el-form>

        <div class="demo-box">
          <div class="demo-head">
            <span>演示账号</span>
            <span class="demo-tip">点击自动填充</span>
          </div>
          <div class="demo-accounts">
            <button
              v-for="account in accounts"
              :key="account.username"
              type="button"
              class="account-chip"
              @click="fill(account)"
            >
              <span class="account-role">{{ account.role }}</span>
              <span class="account-name mono">{{ account.username }}</span>
            </button>
          </div>
          <p class="demo-note">默认密码见账号说明，仅用于本地演示环境。</p>
        </div>

        <div class="form-foot">
          <span>软件工程大作业 · Demo</span>
          <span>v1.0.0</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import { setAuth } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })

const accounts = [
  { role: '管理员', username: 'admin', password: 'admin123' },
  { role: '检测工程师', username: 'engineer', password: 'engineer123' },
  { role: '查阅人员', username: 'viewer', password: 'viewer123' }
]

function fill(account) {
  form.username = account.username
  form.password = account.password
}

async function submit() {
  if (loading.value) return
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号与密码')
    return
  }
  loading.value = true
  try {
    const data = await authApi.login({ ...form })
    setAuth(data)
    ElMessage.success(`欢迎回来，${data.user.display_name}`)
    router.push(route.query.redirect || '/dashboard')
  } catch {
    /* 错误信息由拦截器统一展示 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(420px, 0.82fr);
  background: var(--paper);
}

.login-brand {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 34px 48px 30px;
  color: #e7eff5;
  background:
    radial-gradient(circle at 80% 8%, rgba(217, 164, 65, 0.2), transparent 22rem),
    radial-gradient(circle at 8% 85%, rgba(47, 102, 144, 0.28), transparent 24rem),
    linear-gradient(140deg, #0a1d30 0%, #102f4b 55%, #0c2238 100%);
}

.blueprint-grid {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px) 0 0 / 34px 34px,
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px) 0 0 / 34px 34px;
  mask-image: linear-gradient(120deg, transparent 0%, #000 30%, #000 75%, transparent 100%);
}

.brand-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-title {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #fff;
}

.brand-sub {
  margin-top: 5px;
  font-size: 9px;
  letter-spacing: 0.19em;
  color: #8ba4b8;
}

.brand-main {
  position: relative;
  z-index: 1;
  max-width: 560px;
  margin: auto 0;
  padding: 44px 0 30px;
}

.kicker {
  font-size: 9.5px;
  letter-spacing: 0.24em;
  color: var(--gold);
}

h1 {
  margin: 18px 0 18px;
  font-size: clamp(40px, 4.4vw, 62px);
  line-height: 1.13;
  letter-spacing: 0.06em;
  font-weight: 700;
  color: #f4f8fb;
}

h1 span {
  color: #e2bd76;
}

.brand-desc {
  max-width: 500px;
  font-size: 13px;
  line-height: 1.95;
  color: #9fb4c4;
}

.feature-list {
  display: grid;
  gap: 17px;
  margin-top: 34px;
}

.feature {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.feature-index {
  flex: 0 0 34px;
  padding-top: 2px;
  font-family: "Bahnschrift", sans-serif;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--gold);
  border-top: 1px solid rgba(217, 164, 65, 0.45);
}

.feature strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #e9f1f6;
  letter-spacing: 0.04em;
}

.feature p {
  margin-top: 5px;
  font-size: 11.5px;
  line-height: 1.7;
  color: #8ea4b5;
}

.brand-foot {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 34px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-metric strong {
  display: block;
  font-size: 22px;
  font-weight: 500;
  color: #f1e3c3;
}

.brand-metric span {
  display: block;
  margin-top: 4px;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: #8098aa;
}

.beam-art {
  position: absolute;
  right: -40px;
  bottom: 34px;
  width: min(46vw, 520px);
  opacity: 0.85;
  pointer-events: none;
}

.login-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 42px;
  background:
    radial-gradient(circle at 100% 0%, rgba(29, 74, 107, 0.06), transparent 22rem),
    linear-gradient(180deg, #f8f4ec, #f1ece2);
}

.form-wrap {
  width: min(100%, 388px);
}

.form-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.form-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  color: #f4e6c8;
  font-size: 19px;
  font-weight: 700;
  background: linear-gradient(145deg, var(--navy-800), var(--navy-700));
  box-shadow: 0 8px 20px rgba(15, 39, 66, 0.18);
}

.form-head h2 {
  font-size: 21px;
  letter-spacing: 0.04em;
  color: var(--navy-900);
}

.form-head p {
  margin-top: 5px;
  font-size: 11.5px;
  color: var(--muted);
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #5b6770;
  letter-spacing: 0.06em;
  padding-bottom: 6px;
}

:deep(.el-input__wrapper) {
  padding: 4px 14px;
  background: rgba(255, 253, 248, 0.86);
}

.submit-btn {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  font-size: 14px;
  letter-spacing: 0.16em;
  background: linear-gradient(100deg, var(--navy-800), var(--navy-700));
  border: none;
}

.demo-box {
  margin-top: 26px;
  padding: 16px;
  border: 1px dashed #d8d0c0;
  border-radius: 9px;
  background: rgba(255, 253, 248, 0.55);
}

.demo-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #5b6770;
}

.demo-tip {
  font-weight: 400;
  color: #9a9a92;
}

.demo-accounts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
}

.account-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  padding: 9px 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #fffdf8;
  cursor: pointer;
  transition: border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.account-chip:hover {
  border-color: var(--gold);
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(20, 42, 61, 0.07);
}

.account-role {
  font-size: 10px;
  color: var(--muted);
}

.account-name {
  font-size: 11px;
  color: var(--navy-800);
}

.demo-note {
  margin-top: 10px;
  font-size: 10px;
  color: #9b9a91;
}

.form-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 34px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: #a3a198;
}

@media (max-width: 1080px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-brand {
    min-height: 300px;
    padding: 26px 28px;
  }

  .brand-main {
    margin: 24px 0 10px;
    padding: 12px 0;
  }

  .feature-list,
  .beam-art {
    display: none;
  }

  .brand-foot {
    padding-top: 16px;
    gap: 22px;
  }

  .login-panel {
    padding: 34px 22px 44px;
  }
}
</style>
