import { expect, test } from '@playwright/test'
import { createAndLoginViaUI, gotoWithHydration } from './e2e-helpers'

test('runtime smoke: landing -> protected redirect -> login success', async ({
  page,
}, testInfo) => {
  await gotoWithHydration(page, '/')
  await expect(page.getByRole('link', { name: 'QuantPoly' })).toBeVisible()
  await expect(page.getByRole('link', { name: '免费注册' })).toBeVisible()
  await expect(page.getByRole('link', { name: '登录', exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: '已有账号？登录' })).toBeVisible()

  await gotoWithHydration(page, '/dashboard')
  await page.waitForURL('**/auth/login?next=%2Fdashboard')
  await expect(page.getByRole('heading', { name: '登录' })).toBeVisible()

  await createAndLoginViaUI(page, testInfo)
  await expect(page.getByRole('heading', { name: '仪表盘' })).toBeVisible()
})
