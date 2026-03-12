import { defineConfig, devices } from '@playwright/test'

// 避免与常见本地服务（含其他 vinxi/vite 项目）端口冲突
const PORT = Number(process.env.PLAYWRIGHT_PORT ?? 3002)
const baseURL = `http://localhost:${PORT}`

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list']],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `npm run dev -- --port ${PORT}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      ...process.env,
      // 在 e2e 测试中使用 Playwright mock backend 拦截该 origin 的请求
      VITE_BACKEND_ORIGIN: 'http://127.0.0.1:8000',
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
