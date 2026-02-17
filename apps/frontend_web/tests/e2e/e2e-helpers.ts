import { randomUUID } from 'crypto'
import { expect, type APIResponse, type Page, type TestInfo } from '@playwright/test'

export const HOST = 'localhost'
export const BACKEND_PORT = Number(process.env.PLAYWRIGHT_BACKEND_PORT ?? 8001)
export const BACKEND_URL = `http://${HOST}:${BACKEND_PORT}`

type Envelope<T = unknown> =
  | { success: true; message: string; data?: T }
  | { success: false; error: { code: string; message: string } }

async function readJson(response: APIResponse): Promise<unknown> {
  const text = await response.text()
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`Non-JSON response: status=${response.status()} body=${text.slice(0, 200)}`)
  }
}

async function readEnvelope<T>(response: APIResponse): Promise<Envelope<T>> {
  const json = await readJson(response)
  if (typeof json === 'object' && json !== null && 'success' in json) {
    return json as Envelope<T>
  }
  throw new Error(`Invalid envelope: ${JSON.stringify(json).slice(0, 200)}`)
}

function unwrapEnvelope<T>(envelope: Envelope<T>): T | undefined {
  if (envelope.success) return envelope.data
  throw new Error(`${envelope.error.code}: ${envelope.error.message}`)
}

export async function gotoWithHydration(page: Page, url: string) {
  // TanStack Start SSR needs hydration before event handlers are reliable.
  const hydrated = page
    .waitForResponse((resp) => resp.url().startsWith(`${BACKEND_URL}/users/me`), {
      timeout: 10_000,
    })
    .catch(() => null)

  await page.goto(url)
  await hydrated
}

export function makeE2EUser(testInfo: TestInfo): { email: string; password: string } {
  const email = `e2e+${testInfo.workerIndex}-${Date.now()}-${randomUUID().slice(0, 8)}@example.com`
  // Must satisfy backend password policy: >=8 chars, digit + upper + lower.
  const password = 'Pass1234!'
  return { email, password }
}

export async function registerAndVerifyEmail(page: Page, email: string, password: string) {
  const registerResp = await page.request.post(`${BACKEND_URL}/auth/register`, {
    data: { email, password },
  })
  expect(registerResp.ok()).toBeTruthy()

  const verifyResp = await page.request.post(`${BACKEND_URL}/auth/verify-email`, {
    data: { email },
  })
  expect(verifyResp.ok()).toBeTruthy()
}

export async function createAndLoginViaUI(
  page: Page,
  testInfo: TestInfo,
  options?: { next?: string },
): Promise<{ email: string; password: string }> {
  const { email, password } = makeE2EUser(testInfo)
  await registerAndVerifyEmail(page, email, password)

  const next = options?.next ? `?next=${encodeURIComponent(options.next)}` : ''
  await gotoWithHydration(page, `/auth/login${next}`)

  await expect(page.getByRole('heading', { name: '登录' })).toBeVisible()
  await page.getByLabel('邮箱').fill(email)
  await page.getByLabel('密码').fill(password)
  await page.getByRole('button', { name: '登录' }).click()

  const expected = options?.next ?? '/dashboard'
  await page.waitForURL(`**${expected}`)

  return { email, password }
}

export async function apiCreateStrategyFromTemplate(
  page: Page,
  params: { name: string; preferredTemplateIds?: string[] },
): Promise<{ id: string; templateId: string }> {
  const templatesResp = await page.request.get(`${BACKEND_URL}/strategies/templates`)
  const templatesEnv = await readEnvelope<Array<{ templateId: string; defaults?: Record<string, unknown> }>>(
    templatesResp,
  )
  const templates = unwrapEnvelope(templatesEnv) ?? []
  if (templates.length === 0) throw new Error('No strategy templates from backend')

  const preferred = params.preferredTemplateIds ?? []
  const chosen =
    preferred
      .map((id) => templates.find((t) => t.templateId === id))
      .find(Boolean) ?? templates[0]
  if (!chosen) throw new Error('Failed to choose a strategy template')

  const createResp = await page.request.post(`${BACKEND_URL}/strategies/from-template`, {
    data: {
      name: params.name,
      templateId: chosen.templateId,
      parameters: chosen.defaults ?? {},
    },
  })
  const createdEnv = await readEnvelope<{ id: string }>(createResp)
  const created = unwrapEnvelope(createdEnv)
  if (!created?.id) throw new Error('Backend did not return strategy id')
  return { id: created.id, templateId: chosen.templateId }
}

export async function apiActivateStrategy(page: Page, strategyId: string): Promise<void> {
  const id = encodeURIComponent(strategyId)
  const resp = await page.request.post(`${BACKEND_URL}/strategies/${id}/activate`)
  expect(resp.ok()).toBeTruthy()
}

export async function apiCreateBacktestTask(
  page: Page,
  params: { strategyId: string; config: Record<string, unknown> },
): Promise<{ id: string }> {
  const resp = await page.request.post(`${BACKEND_URL}/backtests`, {
    data: { strategyId: params.strategyId, config: params.config },
  })
  const env = await readEnvelope<{ id: string }>(resp)
  const created = unwrapEnvelope(env)
  if (!created?.id) throw new Error('Backend did not return backtest id')
  return { id: created.id }
}

export async function apiTransitionBacktest(
  page: Page,
  params: {
    taskId: string
    toStatus: 'running' | 'completed' | 'failed' | 'cancelled' | 'pending'
    metrics?: Record<string, number>
  },
): Promise<void> {
  const id = encodeURIComponent(params.taskId)
  const resp = await page.request.post(`${BACKEND_URL}/backtests/${id}/transition`, {
    data: { toStatus: params.toStatus, metrics: params.metrics },
  })
  expect(resp.ok()).toBeTruthy()
}

export async function apiCreateCompletedBacktestViaTaskRunner(
  page: Page,
  params: { strategyId: string; config: Record<string, unknown> },
): Promise<{ taskId: string; status: string }> {
  const resp = await page.request.post(`${BACKEND_URL}/backtests/tasks`, {
    data: { strategyId: params.strategyId, config: params.config },
  })
  const env = await readEnvelope<{ backtestTask?: { id: string; status: string } }>(resp)
  const data = unwrapEnvelope(env)
  const task = data?.backtestTask
  if (!task?.id) throw new Error('Backend did not return backtestTask payload')
  return { taskId: task.id, status: task.status }
}

export async function apiCreateTradingAccount(
  page: Page,
  params: { accountName: string; initialCapital: number },
): Promise<{ id: string }> {
  const resp = await page.request.post(`${BACKEND_URL}/trading/accounts`, {
    data: { accountName: params.accountName, initialCapital: params.initialCapital },
  })
  const env = await readEnvelope<{ id: string }>(resp)
  const account = unwrapEnvelope(env)
  if (!account?.id) throw new Error('Backend did not return trading account id')
  return { id: account.id }
}

export async function apiGenerateSignals(
  page: Page,
  params: { strategyId: string; accountId: string; symbols: string[]; side?: string },
): Promise<void> {
  const resp = await page.request.post(`${BACKEND_URL}/signals/generate`, {
    data: {
      strategyId: params.strategyId,
      accountId: params.accountId,
      symbols: params.symbols,
      side: params.side ?? 'BUY',
    },
  })
  expect(resp.ok()).toBeTruthy()
}

export interface UnresolvedRiskAlert {
  id: string
  ruleName: string
  message: string
  status: string
}

export async function apiListUnresolvedRiskAlerts(page: Page): Promise<UnresolvedRiskAlert[]> {
  const resp = await page.request.get(`${BACKEND_URL}/risk/alerts`, {
    params: { unresolvedOnly: true },
  })
  const env = await readEnvelope<UnresolvedRiskAlert[]>(resp)
  return unwrapEnvelope(env) ?? []
}
