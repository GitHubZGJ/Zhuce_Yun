import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000'
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const OUT_DIR = path.resolve('../evidence/ui')
fs.mkdirSync(OUT_DIR, { recursive: true })

const consoleErrors = []
const apiErrors = []
const steps = []

function assert(condition, message) {
  if (!condition) throw new Error(`断言失败：${message}`)
}

async function main() {
  const browser = await chromium.launch({
    executablePath: EDGE,
    headless: true,
    args: ['--disable-gpu', '--hide-scrollbars']
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    locale: 'zh-CN',
    deviceScaleFactor: 1
  })
  const page = await context.newPage()

  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  page.on('pageerror', (error) => consoleErrors.push(`pageerror: ${error.message}`))
  page.on('response', (response) => {
    if (response.url().includes('/api/') && response.status() >= 400) {
      apiErrors.push(`${response.status()} ${response.url()}`)
    }
  })

  async function snap(name, fullPage = true) {
    await page.locator('.el-message').first().waitFor({ state: 'hidden', timeout: 6000 }).catch(() => {})
    await page.waitForTimeout(600)
    const file = path.join(OUT_DIR, name)
    await page.screenshot({ path: file, fullPage })
    const size = fs.statSync(file).size
    assert(size > 10000, `截图 ${name} 体积异常（${size} bytes）`)
    steps.push({ step: name, file, size })
    console.log(`[截图] ${name} (${Math.round(size / 1024)} KB)`)
  }

  // 1. 登录页与登录流程
  await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'networkidle' })
  await page.getByPlaceholder('请输入登录名').waitFor()
  assert((await page.title()).includes('筑测云'), '登录页标题应包含筑测云')
  await snap('01_login.png')

  await page.getByPlaceholder('请输入登录名').fill('admin')
  await page.getByPlaceholder('请输入密码').fill('admin123')
  await page.getByRole('button', { name: '进入工作台' }).click()
  await page.waitForURL(/#\/dashboard/, { timeout: 15000 })
  await page.locator('h1.page-title', { hasText: '数据看板' }).waitFor()
  await page.waitForFunction(
    () => document.body.innerText.includes('85.3') && document.body.innerText.includes('60'),
    { timeout: 20000 }
  )

  // 2. 数据看板
  const dashboardText = await page.locator('body').innerText()
  assert(dashboardText.includes('工程质量态势'), '看板英雄区应出现')
  assert(dashboardText.includes('85.3'), '看板应显示 AI 可靠性 85.3')
  const projectCard = page.locator('.stat-card', { hasText: '工程项目总数' })
  assert((await projectCard.innerText()).includes('6'), 'KPI 项目总数应为 6')
  const recordCard = page.locator('.stat-card', { hasText: '检测记录总数' })
  assert((await recordCard.innerText()).includes('60'), 'KPI 检测记录应为 60')
  await snap('02_dashboard.png')

  // 3. 工程项目：新建并删除一个临时项目
  await page.getByRole('link', { name: '工程项目' }).click()
  await page.locator('h1.page-title', { hasText: '工程项目' }).waitFor()
  await page.getByText('XM-2026-001').first().waitFor()
  await page.getByRole('button', { name: '新建项目' }).click()
  const projectDialog = page.locator('.el-dialog').filter({ hasText: '新建工程项目' })
  await projectDialog.waitFor()
  await projectDialog.getByPlaceholder('如 XM-2026-008').fill('E2E-TEMP-001')
  await projectDialog.getByPlaceholder('工程全称').fill('端到端验证临时项目')
  await projectDialog.locator('.el-form-item').filter({ hasText: '建设单位' }).locator('input').fill('自动化测试单位')
  await projectDialog.locator('.el-form-item').filter({ hasText: '项目地点' }).locator('input').fill('测试路 1 号')
  await projectDialog.locator('.el-form-item').filter({ hasText: '负责人' }).locator('input').fill('测试员')
  await projectDialog.getByRole('button', { name: '保存项目' }).click()
  await page.getByText('项目创建成功').waitFor({ timeout: 10000 })
  const tempRow = page.locator('tr', { hasText: 'E2E-TEMP-001' })
  await tempRow.waitFor()
  assert((await tempRow.innerText()).includes('端到端验证临时项目'), '临时项目应出现在表格中')
  await tempRow.getByRole('button', { name: '删除' }).click()
  const confirmBox = page.locator('.el-message-box')
  await confirmBox.waitFor()
  await confirmBox.getByRole('button', { name: '删除' }).click()
  await page.getByText('项目已删除').waitFor({ timeout: 10000 })
  await tempRow.waitFor({ state: 'detached', timeout: 10000 })
  await snap('03_projects.png')

  // 4. 检测样品
  await page.getByRole('link', { name: '检测样品' }).click()
  await page.locator('h1.page-title', { hasText: '检测样品' }).waitFor()
  await page.waitForFunction(
    () => document.body.innerText.includes('共 24 个样品'),
    { timeout: 15000 }
  )
  await page.getByPlaceholder('搜索样品编号 / 规格 / 项目').fill('YP-260301')
  await page.getByPlaceholder('搜索样品编号 / 规格 / 项目').press('Enter')
  await page.getByText('YP-260301').first().waitFor()
  assert((await page.locator('body').innerText()).includes('共 1 个样品'), '筛选后应只剩 1 个样品')
  await page.getByRole('button', { name: '登记样品' }).click()
  const sampleDialog = page.locator('.el-dialog').filter({ hasText: '登记检测样品' })
  await sampleDialog.waitFor()
  assert(await sampleDialog.getByText('所属项目').first().isVisible(), '样品表单应包含所属项目')
  await snap('04_samples_dialog.png', false)
  await sampleDialog.getByRole('button', { name: '取消' }).click()
  await page.waitForTimeout(400)
  await page.getByRole('button', { name: '重置' }).click()
  await snap('05_samples.png')

  // 5. 检测记录：打开录入弹窗并验证前端判定预览（不提交）
  await page.getByRole('link', { name: '检测记录' }).click()
  await page.locator('h1.page-title', { hasText: '检测记录' }).waitFor()
  await page.waitForFunction(
    () => document.body.innerText.includes('共 60 条记录'),
    { timeout: 15000 }
  )
  await page.getByPlaceholder('搜索样品编号 / 检测项目 / 项目').fill('YP-260301')
  await page.getByPlaceholder('搜索样品编号 / 检测项目 / 项目').press('Enter')
  await page.getByText('YP-260301').first().waitFor()
  await page.getByRole('button', { name: '录入检测' }).click()
  const recordDialog = page.locator('.el-dialog').filter({ hasText: '录入检测记录' })
  await recordDialog.waitFor()
  const standardInput = recordDialog.locator('input[type="number"]').nth(0)
  const measuredInput = recordDialog.locator('input[type="number"]').nth(1)
  await standardInput.fill('30')
  await measuredInput.fill('31')
  await page.waitForTimeout(400)
  assert((await recordDialog.innerText()).includes('预计判定：合格'), '31≥30 应预览为合格')
  await measuredInput.fill('29')
  await page.waitForTimeout(400)
  assert((await recordDialog.innerText()).includes('预计判定：不合格'), '29<30 应预览为不合格')
  await recordDialog.locator('.el-dialog__body').evaluate((el) => { el.scrollTop = el.scrollHeight })
  await page.waitForTimeout(300)
  await snap('06_record_dialog.png', false)
  await recordDialog.getByRole('button', { name: '取消' }).click()
  await page.waitForTimeout(400)
  await page.getByRole('button', { name: '重置' }).click()
  await snap('07_records.png')

  // 6. AI 协作监管
  await page.getByRole('link', { name: 'AI 协作监管' }).click()
  await page.locator('h1.page-title', { hasText: 'AI 协作监管' }).waitFor()
  await page.getByText('综合协作可靠性').waitFor()
  await page.waitForFunction(() => document.body.innerText.includes('85.3'), { timeout: 20000 })
  const aiText = await page.locator('body').innerText()
  assert(aiText.includes('平均失效分'), 'AI 概览应显示平均失效分')
  assert(aiText.includes('85.3'), 'AI 概览应显示综合可靠性 85.3')
  await snap('08_ai_overview.png')

  await page.getByRole('tab', { name: 'AI 任务台账' }).click()
  await page.getByText('可靠性评级材料汇总').waitFor()
  await snap('09_ai_tasks.png')

  await page.getByRole('tab', { name: '缺陷与帕累托' }).click()
  await page.getByText('缺陷帕累托图').waitFor()
  await snap('10_ai_defects.png')

  await page.getByRole('tab', { name: '分级机制' }).click()
  await page.getByText('按软件工程阶段的 AI 任务拆分').waitFor()
  await snap('11_ai_grading.png')

  // 7. 用户管理
  await page.getByRole('link', { name: '用户管理' }).click()
  await page.locator('h1.page-title', { hasText: '用户管理' }).waitFor()
  await page.locator('tbody tr', { hasText: 'admin' }).first().waitFor()
  await snap('12_users.png')

  // 8. 控制台错误与 API 错误核验
  assert(consoleErrors.length === 0, `浏览器控制台出现错误：${consoleErrors.join(' | ')}`)
  assert(apiErrors.length === 0, `API 返回错误：${apiErrors.join(' | ')}`)

  const result = {
    status: 'passed',
    baseUrl: BASE_URL,
    browser: 'Microsoft Edge (headless)',
    verifiedAt: new Date().toISOString(),
    steps,
    consoleErrors,
    apiErrors
  }
  fs.writeFileSync(path.join(OUT_DIR, 'e2e_result.json'), JSON.stringify(result, null, 2), 'utf-8')
  fs.writeFileSync(
    path.join(OUT_DIR, 'e2e_summary.txt'),
    [
      '筑测云端到端验证结果',
      `时间：${result.verifiedAt}`,
      `地址：${BASE_URL}`,
      `浏览器：${result.browser}`,
      `截图：${steps.length} 张`,
      '结论：全部断言通过，无控制台错误、无 API 4xx/5xx。',
      '',
      ...steps.map((item) => `- ${item.step} (${Math.round(item.size / 1024)} KB)`)
    ].join('\n'),
    'utf-8'
  )
  console.log('E2E PASSED')
  await browser.close()
}

main().catch(async (error) => {
  console.error('E2E FAILED:', error.message)
  console.error('consoleErrors:', consoleErrors)
  console.error('apiErrors:', apiErrors)
  process.exit(1)
})
