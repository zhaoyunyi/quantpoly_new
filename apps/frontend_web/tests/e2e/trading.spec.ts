/**
 * E2E: 交易 — 真实后端联通
 *
 * 覆盖场景：
 * 1. 买入/卖出错误映射（INSUFFICIENT_FUNDS / INSUFFICIENT_POSITION）
 * 2. 分析报表：风险评估 PENDING -> evaluate
 * 3. 账户管理页：加载过滤配置 + 创建账户
 */

import { test, expect } from '@playwright/test'
import {
  apiCreateTradingAccount,
  createAndLoginViaUI,
  gotoWithHydration,
} from './e2e-helpers'

test('trading: buy/sell error mapping', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await apiCreateTradingAccount(page, {
    accountName: '主账户',
    initialCapital: 0,
  })

  await gotoWithHydration(page, '/trading')
  await expect(page.getByRole('heading', { name: '交易', exact: true })).toBeVisible()

  // 选择账户
  await page.getByRole('combobox', { name: '交易账户' }).click()
  await page.getByText('主账户').click()

  // 买入资金不足
  await page.getByLabel('标的代码').fill('AAPL')
  await page.getByLabel('数量').fill('1000')
  await page.getByLabel('价格').fill('1000')
  await page.getByRole('button', { name: '确认买入' }).click()
  await expect(page.getByText('可用资金不足，无法完成买入。请存入资金后重试。')).toBeVisible()

  // 卖出持仓不足
  await page.getByRole('button', { name: '卖出' }).click()
  await page.getByLabel('标的代码').fill('AAPL')
  await page.getByLabel('数量').fill('1000')
  await page.getByLabel('价格').fill('100')
  await page.getByRole('button', { name: '确认卖出' }).click()
  await expect(page.getByText('可用持仓不足，无法完成卖出。请确认持仓数量。')).toBeVisible()
})

test('trading: analytics pending -> evaluate', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await apiCreateTradingAccount(page, {
    accountName: '主账户',
    initialCapital: 0,
  })

  await gotoWithHydration(page, '/trading/analytics')
  await expect(page.getByRole('heading', { name: '分析报表' })).toBeVisible()

  await page.getByRole('combobox', { name: '交易账户' }).click()
  await page.getByText('主账户').click()

  await expect(page.getByText('风险评估快照正在生成中，请稍后刷新查看结果。')).toBeVisible()

  await page.getByRole('button', { name: '发起评估' }).click()
  await expect(page.getByText('评估 ID')).toBeVisible()
})

test('trading: accounts page loads filter config and can create account', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await gotoWithHydration(page, '/trading/accounts')

  await expect(page.getByRole('heading', { name: '账户管理' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '过滤配置' })).toBeVisible()

  await page.getByRole('button', { name: '创建账户' }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: '创建交易账户' })).toBeVisible()
  await dialog.getByLabel('账户名称').fill('测试账户')
  await dialog.getByLabel('初始资金（可选）').fill('5000')
  await dialog.getByRole('button', { name: '创建' }).click()
  await expect(dialog).toBeHidden()

  await expect(page.getByText('测试账户')).toBeVisible()
})

