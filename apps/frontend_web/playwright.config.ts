import { defineConfig, devices } from '@playwright/test'

// 避免与常见本地服务（含其他 vinxi/vite 项目）端口冲突
const PORT = Number(process.env.PLAYWRIGHT_PORT ?? 3002)
const FRONTEND_HOST = 'localhost'
const BACKEND_HOST = 'localhost'
const BACKEND_PORT = Number(process.env.PLAYWRIGHT_BACKEND_PORT ?? 8001)
const baseURL = `http://${FRONTEND_HOST}:${PORT}`
const backendURL = `http://${BACKEND_HOST}:${BACKEND_PORT}`

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
  webServer: [
    {
      command: `../../.venv/bin/python ../../scripts/run_backend_server.py --host ${BACKEND_HOST} --port ${BACKEND_PORT}`,
      url: `${backendURL}/health`,
      // E2E requires deterministic in-memory state; avoid reusing an arbitrary local backend.
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        BACKEND_HOST: BACKEND_HOST,
        BACKEND_PORT: String(BACKEND_PORT),
        BACKEND_STORAGE_BACKEND: 'memory',
        // Browser tests need CORS + credentials to carry cookie sessions.
        BACKEND_CORS_ALLOWED_ORIGINS: baseURL,
        BACKEND_CORS_ALLOW_CREDENTIALS: 'true',
        BACKEND_CORS_ALLOW_METHODS: 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
        BACKEND_CORS_ALLOW_HEADERS: '*',
        BACKEND_LOG_LEVEL: process.env.CI ? 'warning' : 'warning',
        BACKEND_REQUIRE_WS_SUPPORT: 'true',
      },
    },
    {
      command: `npm run dev -- --port ${PORT}`,
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_BACKEND_ORIGIN: backendURL,
      },
    },
  ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
