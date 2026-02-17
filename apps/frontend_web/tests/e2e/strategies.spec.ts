/**
 * E2E: 策略管理 — 真实后端联通
 *
 * 覆盖场景：
 * 1. 策略列表：可见 + 创建新策略 + 删除冲突提示（STRATEGY_IN_USE）
 * 2. 向导式创建：选择模板 -> 配置参数 -> 创建 -> 进入详情页
 */

import { test, expect } from '@playwright/test'
import {
  apiCreateBacktestTask,
  apiCreateStrategyFromTemplate,
  createAndLoginViaUI,
  gotoWithHydration,
} from './e2e-helpers'

test('strategies: list + create + delete-conflict', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  // Seed base strategies.
  await apiCreateStrategyFromTemplate(page, {
    name: 'MA策略',
    preferredTemplateIds: ['moving_average'],
  })
  const inUse = await apiCreateStrategyFromTemplate(page, {
    name: '占用策略',
    preferredTemplateIds: ['moving_average'],
  })
  // Seed a pending backtest so deletion will be rejected with STRATEGY_IN_USE.
  await apiCreateBacktestTask(page, {
    strategyId: inUse.id,
    config: { displayName: '占用回测' },
  })

  await gotoWithHydration(page, '/strategies')

  await expect(page.getByRole('heading', { name: '策略管理' })).toBeVisible()
  await expect(page.getByText('MA策略')).toBeVisible()

  // 创建策略（列表页弹窗）
  await page.getByRole('button', { name: '创建策略' }).click()
  const createDialog = page.getByRole('dialog')
  await expect(createDialog.getByRole('heading', { name: '创建策略' })).toBeVisible()

  await createDialog.getByLabel('策略名称').fill('新策略-1')
  await createDialog.getByLabel('策略模板').selectOption('moving_average')
  await createDialog.getByLabel('shortWindow').fill('7')
  await createDialog.getByLabel('longWindow').fill('21')
  await createDialog.getByRole('button', { name: '创建策略' }).click()

  await expect(createDialog).toBeHidden()
  await expect(page.getByText('新策略-1')).toBeVisible()

  // 删除保护：409 STRATEGY_IN_USE
  const inUseRow = page.getByRole('row', { name: /占用策略/ })
  await inUseRow.getByRole('button', { name: '删除' }).click()

  const deleteDialog = page.getByRole('dialog')
  await expect(deleteDialog.getByRole('heading', { name: '确认删除' })).toBeVisible()
  await deleteDialog.getByRole('button', { name: '确认删除' }).click()

  await expect(deleteDialog.getByRole('alert')).toContainText('无法删除')
  await deleteDialog.getByRole('button', { name: '取消' }).click()
  await expect(deleteDialog).toBeHidden()

  // Ensure seeded strategy is still visible.
  await expect(page.getByRole('button', { name: '占用策略', exact: true })).toBeVisible()
})

test('strategies: wizard create -> detail page', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await gotoWithHydration(page, '/strategies/simple')
  await expect(page.getByRole('heading', { name: '向导式创建策略' })).toBeVisible()

  // Step1: 选择模板（moving_average: 双均线）
  await page.getByRole('button', { name: /双均线/ }).click({ force: true })

  // Step2: 配置参数
  await page.getByLabel('策略名称').fill('向导策略-1')
  await page.getByLabel('shortWindow').fill('5')
  await page.getByLabel('longWindow').fill('20')
  await page.getByRole('button', { name: '下一步' }).click()

  // Step3: 确认创建
  await expect(page.getByRole('heading', { name: '确认创建' })).toBeVisible()
  await page.getByRole('button', { name: '确认创建' }).click()

  // 创建成功
  await expect(page.getByRole('heading', { name: /创建成功/ })).toBeVisible()
  await page.getByRole('button', { name: '查看详情' }).click()

  // 详情页
  await expect(page.getByRole('heading', { name: '向导策略-1' })).toBeVisible()
  await expect(page.getByText('策略参数')).toBeVisible()
})
