/**
 * E2E: 回测中心 — 真实后端联通
 *
 * 覆盖场景：
 * 1. 列表页：统计概览 + 列表项可见
 * 2. 创建回测：通过 UI 创建任务并出现在列表
 * 3. 详情页：已完成任务可查看结果
 * 4. 详情页：运行中任务结果未就绪提示
 * 5. 详情页：相关回测区域可见
 */

import { test, expect } from '@playwright/test'
import {
  apiActivateStrategy,
  apiCreateBacktestTask,
  apiCreateCompletedBacktestViaTaskRunner,
  apiCreateStrategyFromTemplate,
  apiTransitionBacktest,
  createAndLoginViaUI,
  gotoWithHydration,
} from './e2e-helpers'

function truncateId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 12)}…` : id
}

function samplePrices(count: number): number[] {
  // simple ascending-ish series; enough length for moving_average longWindow=20 default.
  return Array.from({ length: count }, (_, i) => 100 + i)
}

test('backtests: list page shows statistics and seeded items', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '回测策略-1',
    preferredTemplateIds: ['moving_average'],
  })

  // Create one completed task (needs active strategy + sufficient price series).
  await apiActivateStrategy(page, strategy.id)
  await apiCreateCompletedBacktestViaTaskRunner(page, {
    strategyId: strategy.id,
    config: {
      displayName: '已完成回测',
      symbol: 'AAPL',
      prices: samplePrices(30),
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      timeframe: '1Day',
      initialCapital: 100000,
      commissionRate: 0.0,
    },
  })

  // Create one running task without result.
  const running = await apiCreateBacktestTask(page, {
    strategyId: strategy.id,
    config: { displayName: '运行中回测' },
  })
  await apiTransitionBacktest(page, { taskId: running.id, toStatus: 'running' })

  await gotoWithHydration(page, '/backtests')

  await expect(page.getByRole('heading', { name: '回测中心' })).toBeVisible()

  // 统计概览
  const overviewPanel = page
    .locator('section')
    .filter({ has: page.getByRole('heading', { name: '统计概览' }) })
  await expect(page.getByRole('heading', { name: '统计概览' })).toBeVisible()
  await expect(overviewPanel.getByText('已完成', { exact: true })).toBeVisible()
  await expect(overviewPanel.getByText('运行中', { exact: true })).toBeVisible()

  // 列表项
  await expect(page.getByText('已完成回测')).toBeVisible()
  await expect(page.getByText('运行中回测')).toBeVisible()
})

test('backtests: create backtest via UI -> appears in list', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await apiCreateStrategyFromTemplate(page, {
    name: 'MA策略',
    preferredTemplateIds: ['moving_average'],
  })

  await gotoWithHydration(page, '/backtests')
  await expect(page.getByRole('heading', { name: '回测中心' })).toBeVisible()

  await page.getByRole('button', { name: '创建回测' }).click()

  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: '创建回测' })).toBeVisible()

  // 选择策略
  await dialog.getByRole('combobox', { name: '策略' }).click()
  await page.getByRole('option', { name: 'MA策略' }).click()

  // 捕获创建请求以获取 taskId（列表展示为 truncateId）
  const created = page.waitForResponse((resp) => {
    return resp.url().includes('/backtests') && resp.request().method() === 'POST'
  })

  await dialog.getByRole('button', { name: '提交回测' }).click()

  const resp = await created
  const json = (await resp.json()) as { success: boolean; data?: { id?: string } }
  const taskId = json?.data?.id
  if (!taskId) throw new Error('backend did not return backtest id')

  await expect(dialog).toBeHidden()

  await expect(page.getByRole('button', { name: truncateId(taskId) })).toBeVisible()
})

test('backtests: view completed detail -> shows result section', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '回测策略-2',
    preferredTemplateIds: ['moving_average'],
  })
  await apiActivateStrategy(page, strategy.id)

  const completed = await apiCreateCompletedBacktestViaTaskRunner(page, {
    strategyId: strategy.id,
    config: {
      displayName: '已完成回测',
      symbol: 'AAPL',
      prices: samplePrices(30),
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      timeframe: '1Day',
      initialCapital: 100000,
      commissionRate: 0.0,
    },
  })

  await gotoWithHydration(page, `/backtests/${completed.taskId}`)

  await expect(page.getByRole('heading', { name: '已完成回测' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '回测配置' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '回测结果' })).toBeVisible()
})

test('backtests: running backtest -> result not ready hint', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '回测策略-3',
    preferredTemplateIds: ['moving_average'],
  })

  const running = await apiCreateBacktestTask(page, {
    strategyId: strategy.id,
    config: { displayName: '运行中回测' },
  })
  await apiTransitionBacktest(page, { taskId: running.id, toStatus: 'running' })

  await gotoWithHydration(page, `/backtests/${running.id}`)

  await expect(page.getByRole('heading', { name: '运行中回测' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '回测结果' })).toBeVisible()
  await expect(page.getByRole('button', { name: '刷新结果' })).toBeVisible()
})

test('backtests: related backtests section shows other tasks of same strategy', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  const strategy = await apiCreateStrategyFromTemplate(page, {
    name: '回测策略-4',
    preferredTemplateIds: ['moving_average'],
  })
  await apiActivateStrategy(page, strategy.id)

  const completed = await apiCreateCompletedBacktestViaTaskRunner(page, {
    strategyId: strategy.id,
    config: {
      displayName: '已完成回测',
      symbol: 'AAPL',
      prices: samplePrices(30),
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      timeframe: '1Day',
      initialCapital: 100000,
      commissionRate: 0.0,
    },
  })

  await apiCreateBacktestTask(page, {
    strategyId: strategy.id,
    config: { displayName: '另一个回测' },
  })

  await gotoWithHydration(page, `/backtests/${completed.taskId}`)

  await expect(page.getByRole('heading', { name: '相关回测' })).toBeVisible()
  await expect(page.getByText('另一个回测')).toBeVisible()
})
