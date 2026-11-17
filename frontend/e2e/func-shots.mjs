import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000'
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const OUT_DIR = path.resolve('../evidence/tests')
fs.mkdirSync(OUT_DIR, { recursive: true })

const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--disable-gpu', '--hide-scrollbars'] })
const context = await browser.newContext({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' })
const page = await context.newPage()

async function snap(name) {
  await page.waitForTimeout(500)
  const file = path.join(OUT_DIR, name)
  await page.screenshot({ path: file, fullPage: false })
  console.log('[shot]', name, fs.statSync(file).size)
}

async function login(username, password) {
  await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'networkidle' })
  await page.getByPlaceholder('请输入登录名').fill(username)
  await page.getByPlaceholder('请输入密码').fill(password)
  await page.getByRole('button', { name: '进入工作台' }).click()
  await page.waitForURL(/#\/dashboard/, { timeout: 15000 })
  await page.waitForTimeout(1200)
}

// 1) 功能测试：新增项目（含成功提示与表格新行），随后删除恢复数据
await login('admin', 'admin123')
await page.getByRole('link', { name: '工程项目' }).click()
await page.waitForTimeout(1000)
await page.getByRole('button', { name: '新建项目' }).click()
const dlg = page.locator('.el-dialog').filter({ hasText: '新建工程项目' })
await dlg.waitFor()
await dlg.getByPlaceholder('如 XM-2026-008').fill('FUNC-2026-001')
await dlg.getByPlaceholder('工程全称').fill('功能测试临时项目')
await dlg.locator('.el-form-item').filter({ hasText: '建设单位' }).locator('input').fill('功能测试单位')
await dlg.locator('.el-form-item').filter({ hasText: '项目地点' }).locator('input').fill('测试路 1 号')
await dlg.locator('.el-form-item').filter({ hasText: '负责人' }).locator('input').fill('测试员')
await dlg.getByRole('button', { name: '保存项目' }).click()
await page.getByText('项目创建成功').waitFor({ timeout: 10000 })
const row = page.locator('tr', { hasText: 'FUNC-2026-001' })
await row.waitFor()
await snap('func_01_project_create.png')
await row.getByRole('button', { name: '删除' }).click()
const box = page.locator('.el-message-box')
await box.waitFor()
await box.getByRole('button', { name: '删除' }).click()
await page.getByText('项目已删除').waitFor({ timeout: 10000 })
await row.waitFor({ state: 'detached', timeout: 10000 })

// 2) 功能测试：录入检测记录并自动判定（合格），随后删除恢复数据
await page.getByRole('link', { name: '检测记录' }).click()
await page.waitForTimeout(1000)
await page.getByRole('button', { name: '录入检测' }).click()
const rdlg = page.locator('.el-dialog').filter({ hasText: '录入检测记录' })
await rdlg.waitFor()
const sampleSelect = rdlg.locator('.el-form-item').filter({ hasText: '检测样品' }).locator('.el-select')
await sampleSelect.click()
await page.keyboard.type('YP-260301')
await page.waitForTimeout(600)
await page.locator('.el-select-dropdown__item', { hasText: 'YP-260301' }).first().click()
await rdlg.locator('.el-form-item').filter({ hasText: '检测项目' }).locator('input').fill('抗压强度（28d）')
await rdlg.locator('.el-form-item').filter({ hasText: '计量单位' }).locator('input').fill('MPa')
const nums = rdlg.locator('input[type="number"]')
await nums.nth(0).fill('30')
await nums.nth(1).fill('31')
await page.waitForTimeout(400)
await rdlg.getByRole('button', { name: '保存并判定' }).click()
await page.getByText('检测记录已保存，判定结果：合格').waitFor({ timeout: 10000 })
await page.waitForTimeout(800)
await snap('func_02_record_create_pass.png')
const recRow = page.locator('tr', { hasText: 'YP-260301' }).first()
await recRow.getByRole('button', { name: '删除' }).click()
const box2 = page.locator('.el-message-box')
await box2.waitFor()
await box2.getByRole('button', { name: '删除' }).click()
await page.getByText('检测记录已删除').waitFor({ timeout: 10000 })

// 3) 权限测试：查阅人员只读（无新建/编辑/删除入口）
await page.locator('.user-trigger').click()
await page.getByText('退出登录').click()
await page.waitForURL(/#\/login/, { timeout: 10000 })
await login('viewer', 'viewer123')
await page.getByRole('link', { name: '工程项目' }).click()
await page.waitForTimeout(1200)
const bodyText = await page.locator('body').innerText()
if (bodyText.includes('新建项目')) throw new Error('查阅人员不应看到新建项目按钮')
await snap('func_03_viewer_readonly.png')

await browser.close()
console.log('FUNC SHOTS DONE')
