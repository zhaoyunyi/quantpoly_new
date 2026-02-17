/**
 * E2E: 实时监控 — 真实后端联通
 *
 * 覆盖场景：
 * 1. Monitor 页面加载并建立 WS 连接
 * 2. Signals 面板展示 pending 信号
 * 3. WS 连接建立后，新增信号可自动推送到列表（无需手动刷新）
 * 4. Alerts 面板基于真实后端返回展示（有告警展示列表，无告警展示空态）
 * 5. Operational Summary 区域可见
 */

import { test, expect, type Page } from '@playwright/test'
import {
  BACKEND_URL,
  apiCreateTradingAccount,
  apiCreateStrategyFromTemplate,
  apiGenerateSignals,
  apiListUnresolvedRiskAlerts,
  createAndLoginViaUI,
  gotoWithHydration,
} from './e2e-helpers'

async function seedAlertByRuleAndAssess(
  page: Page,
  accountId: string,
): Promise<void> {
  const createRule = await page.request.post(`${BACKEND_URL}/risk/rules`, {
    data: {
      accountId,
      ruleName: '仓位过于集中',
      threshold: 0.8,
    },
  })
  expect(createRule.ok()).toBeTruthy()

  const assess = await page.request.post(`${BACKEND_URL}/risk/check/account/${encodeURIComponent(accountId)}`)
  expect(assess.ok()).toBeTruthy()
}

test('monitor: page loads with connection badge + sections', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await gotoWithHydration(page, '/monitor')

  await expect(page.getByRole('heading', { name: '实时监控' })).toBeVisible()
  await expect(page.getByText('已连接')).toBeVisible({ timeout: 20_000 })
  await expect(page.getByRole('heading', { name: 'Signals' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Alerts' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Operational Summary' })).toBeVisible()
})

test('monitor: signals list shows pending signals from backend', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const account = await apiCreateTradingAccount(page, {
    accountName: '监控账户',
    initialCapital: 10000,
  })
  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '监控策略',
    preferredTemplateIds: ['moving_average'],
  })

  await apiGenerateSignals(page, {
    strategyId: strategy.id,
    accountId: account.id,
    symbols: ['AAPL', 'TSLA'],
    side: 'BUY',
  })

  await gotoWithHydration(page, '/monitor')
  await expect(page.getByRole('heading', { name: '实时监控' })).toBeVisible()

  const signalsPanel = page.locator('section', {
    has: page.getByRole('heading', { name: 'Signals' }),
  })
  await expect(signalsPanel.getByRole('cell', { name: 'AAPL', exact: true })).toBeVisible({
    timeout: 20_000,
  })
  await expect(signalsPanel.getByRole('cell', { name: 'TSLA', exact: true })).toBeVisible()
})

test('monitor: websocket pushes newly generated signal without manual refresh', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const account = await apiCreateTradingAccount(page, {
    accountName: '实时推送账户',
    initialCapital: 10000,
  })
  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '实时推送策略',
    preferredTemplateIds: ['moving_average'],
  })

  await gotoWithHydration(page, '/monitor')
  await expect(page.getByRole('heading', { name: '实时监控' })).toBeVisible()
  await expect(page.getByText('已连接')).toBeVisible({ timeout: 20_000 })

  const signalsPanel = page.locator('section', {
    has: page.getByRole('heading', { name: 'Signals' }),
  })
  await expect(signalsPanel.getByText('暂无待处理信号')).toBeVisible()

  await apiGenerateSignals(page, {
    strategyId: strategy.id,
    accountId: account.id,
    symbols: ['NVDA'],
    side: 'BUY',
  })

  // useMonitorSocket 每 5s poll 一次；给充足窗口等待增量 push。
  await expect(signalsPanel.getByRole('cell', { name: 'NVDA', exact: true })).toBeVisible({
    timeout: 20_000,
  })
})

test('monitor: alerts list shows unresolved alerts from backend', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const account = await apiCreateTradingAccount(page, {
    accountName: '告警账户',
    initialCapital: 10000,
  })
  await seedAlertByRuleAndAssess(page, account.id)
  const unresolved = await apiListUnresolvedRiskAlerts(page)

  await gotoWithHydration(page, '/monitor')
  await expect(page.getByRole('heading', { name: '实时监控' })).toBeVisible()

  const alertsPanel = page.locator('section', {
    has: page.getByRole('heading', { name: 'Alerts' }),
  })
  if (unresolved.length > 0) {
    await expect(
      alertsPanel.getByRole('cell', { name: unresolved[0].ruleName, exact: true }),
    ).toBeVisible({ timeout: 20_000 })
    return
  }

  // 当前真实后端实现下，risk assess 仅产出评估快照，不会自动创建 alert。
  await expect(alertsPanel.getByText('暂无未解决告警')).toBeVisible({ timeout: 20_000 })
})

test('monitor: operational summary bar displays stats', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await gotoWithHydration(page, '/monitor')

  await expect(page.getByRole('heading', { name: 'Operational Summary' })).toBeVisible()
  await expect(page.locator('[data-mono]').first()).toBeVisible({ timeout: 10_000 })
})
