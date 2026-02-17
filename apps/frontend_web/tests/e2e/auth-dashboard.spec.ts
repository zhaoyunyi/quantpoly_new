/**
 * E2E: Auth -> Dashboard
 *
 * These tests run against a real backend HTTP server (see playwright.config.ts webServer).
 */

import { test, expect } from '@playwright/test'
import { createAndLoginViaUI, gotoWithHydration, makeE2EUser } from './e2e-helpers'

test('login: success -> dashboard with KPI cards', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo)

  await expect(page.getByRole('heading', { name: '仪表盘' })).toBeVisible()

  // KPI cards (use accessible name to avoid strict-mode collisions)
  await expect(page.getByRole('link', { name: /^账户\s/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /^策略\s/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /^回测\s/ })).toBeVisible()

  // Panels
  await expect(page.getByRole('heading', { name: '资产概览' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '回测统计' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '告警统计' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '信号统计' })).toBeVisible()
})

test('login: failure shows error message', async ({ page }, testInfo) => {
  const { email } = makeE2EUser(testInfo)
  await gotoWithHydration(page, '/auth/login')

  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码').fill('wrong-password')
  await page.getByRole('button', { name: '登录' }).click()

  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByText('邮箱或密码不正确')).toBeVisible()
  await expect(page.getByRole('heading', { name: '登录' })).toBeVisible()
})

test('login: redirect to next param after success', async ({ page }, testInfo) => {
  await createAndLoginViaUI(page, testInfo, { next: '/strategies' })

  await expect(page.getByRole('heading', { name: '策略管理' })).toBeVisible()
})
