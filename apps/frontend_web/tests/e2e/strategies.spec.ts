import { test, expect, type Page, type Request } from '@playwright/test'

type StrategyStatus = 'draft' | 'active' | 'inactive' | 'archived'

interface StrategyTemplate {
  templateId: string
  name: string
  requiredParameters: Record<
    string,
    {
      type: string
      min?: number
      max?: number
    }
  >
  defaults?: Record<string, unknown>
}

interface StrategyItem {
  id: string
  userId: string
  name: string
  template: string
  parameters: Record<string, unknown>
  status: StrategyStatus
  createdAt: string
  updatedAt: string
}

interface StrategyBacktest {
  id: string
  userId: string
  strategyId: string
  status: string
  config: Record<string, unknown>
  metrics: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

const FRONTEND_ORIGIN = 'http://127.0.0.1:3000'
const BACKEND_ORIGIN = 'http://127.0.0.1:8000'

function success<T>(data: T, message = 'ok') {
  return { success: true as const, message, data }
}

function failure(code: string, message: string) {
  return { success: false as const, error: { code, message } }
}

function nowIso(): string {
  // 固定到秒，避免 UI 显示/快照抖动
  return new Date(Math.floor(Date.now() / 1000) * 1000).toISOString()
}

function corsHeaders(req: Request): Record<string, string> {
  const origin = req.headers()['origin'] ?? FRONTEND_ORIGIN
  return {
    'access-control-allow-origin': origin,
    'access-control-allow-credentials': 'true',
    vary: 'Origin',
  }
}

function preflightHeaders(req: Request): Record<string, string> {
  const allowHeaders =
    req.headers()['access-control-request-headers'] ?? 'content-type'
  return {
    ...corsHeaders(req),
    'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    'access-control-allow-headers': allowHeaders,
  }
}

async function installMockBackend(page: Page) {
  const me = {
    id: 'u-1',
    email: 'u1@test.com',
    displayName: 'U1',
    isActive: true,
    emailVerified: true,
    role: 'user',
    level: 1,
  }

  const templates: StrategyTemplate[] = [
    {
      templateId: 'tpl-ma-cross',
      name: '均线交叉',
      requiredParameters: {
        shortPeriod: { type: 'integer', min: 1, max: 200 },
        longPeriod: { type: 'integer', min: 2, max: 500 },
      },
      defaults: { shortPeriod: 5, longPeriod: 20 },
    },
    {
      templateId: 'tpl-rsi',
      name: 'RSI 反转',
      requiredParameters: {
        period: { type: 'integer', min: 2, max: 100 },
      },
      defaults: { period: 14 },
    },
  ]

  const strategies: StrategyItem[] = [
    {
      id: 's-1',
      userId: me.id,
      name: 'MA策略',
      template: 'tpl-ma-cross',
      parameters: { shortPeriod: 5, longPeriod: 20 },
      status: 'active',
      createdAt: '2026-01-01T00:00:00Z',
      updatedAt: '2026-01-02T00:00:00Z',
    },
    {
      id: 's-in-use',
      userId: me.id,
      name: '占用策略',
      template: 'tpl-rsi',
      parameters: { period: 14 },
      status: 'draft',
      createdAt: '2026-01-03T00:00:00Z',
      updatedAt: '2026-01-04T00:00:00Z',
    },
    {
      id: 's-archived',
      userId: me.id,
      name: '已归档策略',
      template: 'tpl-ma-cross',
      parameters: { shortPeriod: 10, longPeriod: 30 },
      status: 'archived',
      createdAt: '2026-01-05T00:00:00Z',
      updatedAt: '2026-01-06T00:00:00Z',
    },
  ]

  const backtestsByStrategy = new Map<string, StrategyBacktest[]>()
  let nextStrategySeq = 100
  let nextBacktestSeq = 1

  function listStrategies(url: URL) {
    const status = url.searchParams.get('status') || undefined
    const search = url.searchParams.get('search') || undefined
    const page = Number(url.searchParams.get('page') || 1)
    const pageSize = Number(url.searchParams.get('pageSize') || 20)

    let filtered = [...strategies]
    if (status) filtered = filtered.filter((s) => s.status === status)
    if (search)
      filtered = filtered.filter((s) =>
        s.name.toLowerCase().includes(search.toLowerCase()),
      )

    const total = filtered.length
    const start = Math.max(0, (page - 1) * pageSize)
    const items = filtered.slice(start, start + pageSize)
    return { items, total, page, pageSize }
  }

  async function handleApi(req: Request): Promise<{ status: number; body: unknown }> {
    const url = new URL(req.url())
    if (url.origin !== BACKEND_ORIGIN) {
      return { status: 404, body: failure('NOT_FOUND', 'unknown origin') }
    }

    const parts = url.pathname.split('/').filter(Boolean)
    const method = req.method()

    // GET /users/me
    if (method === 'GET' && url.pathname === '/users/me') {
      return { status: 200, body: success(me) }
    }

    // GET /strategies/templates
    if (method === 'GET' && url.pathname === '/strategies/templates') {
      return { status: 200, body: success(templates) }
    }

    // GET /strategies?page&pageSize&status&search
    if (parts.length === 1 && parts[0] === 'strategies' && method === 'GET') {
      return { status: 200, body: success(listStrategies(url)) }
    }

    // POST /strategies
    if (parts.length === 1 && parts[0] === 'strategies' && method === 'POST') {
      const payload = req.postDataJSON() as {
        name: string
        template: string
        parameters: Record<string, unknown>
      }
      const ts = nowIso()
      const created: StrategyItem = {
        id: `s-${nextStrategySeq++}`,
        userId: me.id,
        name: payload.name,
        template: payload.template,
        parameters: payload.parameters ?? {},
        status: 'draft',
        createdAt: ts,
        updatedAt: ts,
      }
      strategies.unshift(created)
      return { status: 200, body: success(created) }
    }

    // POST /strategies/from-template
    if (
      parts.length === 2 &&
      parts[0] === 'strategies' &&
      parts[1] === 'from-template' &&
      method === 'POST'
    ) {
      const payload = req.postDataJSON() as {
        name: string
        templateId: string
        parameters: Record<string, unknown>
      }
      const ts = nowIso()
      const created: StrategyItem = {
        id: `s-${nextStrategySeq++}`,
        userId: me.id,
        name: payload.name,
        template: payload.templateId,
        parameters: payload.parameters ?? {},
        status: 'draft',
        createdAt: ts,
        updatedAt: ts,
      }
      strategies.unshift(created)
      return { status: 200, body: success(created) }
    }

    // /strategies/:id/...
    if (parts.length >= 2 && parts[0] === 'strategies') {
      const id = decodeURIComponent(parts[1] ?? '')
      const strategy = strategies.find((s) => s.id === id)
      const ts = nowIso()

      if (!strategy) {
        return { status: 404, body: failure('NOT_FOUND', 'strategy not found') }
      }

      // GET /strategies/:id
      if (parts.length === 2 && method === 'GET') {
        return { status: 200, body: success(strategy) }
      }

      // PUT /strategies/:id
      if (parts.length === 2 && method === 'PUT') {
        const payload = req.postDataJSON() as {
          name?: string
          parameters?: Record<string, unknown>
        }
        strategy.name = payload.name ?? strategy.name
        strategy.parameters = payload.parameters ?? strategy.parameters
        strategy.updatedAt = ts
        return { status: 200, body: success(strategy) }
      }

      // DELETE /strategies/:id
      if (parts.length === 2 && method === 'DELETE') {
        if (id === 's-in-use') {
          return {
            status: 409,
            body: failure(
              'STRATEGY_IN_USE',
              '该策略有正在运行或排队中的回测任务',
            ),
          }
        }
        const idx = strategies.findIndex((s) => s.id === id)
        if (idx >= 0) strategies.splice(idx, 1)
        return { status: 200, body: success({ deleted: true }) }
      }

      // POST /strategies/:id/activate|deactivate|archive
      if (method === 'POST' && parts.length === 3) {
        if (parts[2] === 'activate') strategy.status = 'active'
        if (parts[2] === 'deactivate') strategy.status = 'inactive'
        if (parts[2] === 'archive') strategy.status = 'archived'
        strategy.updatedAt = ts
        return { status: 200, body: success(strategy) }
      }

      // POST /strategies/:id/validate-execution
      if (method === 'POST' && parts.length === 3 && parts[2] === 'validate-execution') {
        return {
          status: 200,
          body: success({
            valid: true,
            strategyId: id,
            template: strategy.template,
          }),
        }
      }

      // GET|POST /strategies/:id/backtests
      if (parts.length === 3 && parts[2] === 'backtests') {
        const list = backtestsByStrategy.get(id) ?? []

        if (method === 'GET') {
          const page = Number(url.searchParams.get('page') || 1)
          const pageSize = Number(url.searchParams.get('pageSize') || 20)
          const status = url.searchParams.get('status') || undefined
          const filtered = status ? list.filter((b) => b.status === status) : list
          return {
            status: 200,
            body: success({
              items: filtered.slice(0, pageSize),
              total: filtered.length,
              page,
              pageSize,
            }),
          }
        }

        if (method === 'POST') {
          const payload = req.postDataJSON() as { config?: Record<string, unknown> }
          const bt: StrategyBacktest = {
            id: `bt-${nextBacktestSeq++}`,
            userId: me.id,
            strategyId: id,
            status: 'pending',
            config: payload?.config ?? {},
            metrics: {},
            createdAt: ts,
            updatedAt: ts,
          }
          list.unshift(bt)
          backtestsByStrategy.set(id, list)
          return { status: 200, body: success(bt) }
        }
      }

      // GET /strategies/:id/backtest-stats
      if (method === 'GET' && parts.length === 3 && parts[2] === 'backtest-stats') {
        const list = backtestsByStrategy.get(id) ?? []
        const stats = {
          pendingCount: list.filter((b) => b.status === 'pending').length,
          runningCount: list.filter((b) => b.status === 'running').length,
          completedCount: list.filter((b) => b.status === 'completed').length,
          failedCount: list.filter((b) => b.status === 'failed').length,
          cancelledCount: list.filter((b) => b.status === 'cancelled').length,
          totalCount: list.length,
          averageReturnRate: 0.1234,
          averageMaxDrawdown: 0.0567,
          averageWinRate: 0.61,
        }
        return { status: 200, body: success(stats) }
      }

      // POST /strategies/:id/research/*
      if (parts.length === 4 && parts[2] === 'research' && method === 'POST') {
        const taskType =
          parts[3] === 'performance-task'
            ? 'performance'
            : parts[3] === 'optimization-task'
              ? 'optimization'
              : 'unknown'
        return {
          status: 200,
          body: success({
            taskId: `r-${taskType}-1`,
            taskType,
            status: 'queued',
            result: null,
          }),
        }
      }

      // GET /strategies/:id/research/results
      if (parts.length === 4 && parts[2] === 'research' && parts[3] === 'results' && method === 'GET') {
        return {
          status: 200,
          body: success({ items: [], total: 0 }),
        }
      }
    }

    // POST /backtests/compare
    if (parts.length === 2 && parts[0] === 'backtests' && parts[1] === 'compare' && req.method() === 'POST') {
      const payload = req.postDataJSON() as { taskIds: string[] }
      return {
        status: 200,
        body: success({
          taskIds: payload.taskIds ?? [],
          metrics: (payload.taskIds ?? []).map((_, idx) => ({
            returnRate: 0.1 + idx * 0.05,
            maxDrawdown: 0.2,
            winRate: 0.55,
          })),
        }),
      }
    }

    return { status: 404, body: failure('NOT_FOUND', 'unknown endpoint') }
  }

  await page.route(`${BACKEND_ORIGIN}/**`, async (route) => {
    const req = route.request()
    if (req.method() === 'OPTIONS') {
      await route.fulfill({
        status: 204,
        headers: preflightHeaders(req),
        body: '',
      })
      return
    }

    const { status, body } = await handleApi(req)
    await route.fulfill({
      status,
      headers: {
        ...corsHeaders(req),
        'content-type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(body),
    })
  })
}

test('strategies: list + create + delete-conflict', async ({ page }) => {
  await installMockBackend(page)

  await page.goto('/strategies')

  // AuthGuard 通过后会渲染 AppShell + 页面标题
  await expect(page.getByRole('heading', { name: '策略管理' })).toBeVisible()
  await expect(page.getByText('MA策略')).toBeVisible()

  // 创建策略（列表页弹窗）
  await page.getByRole('button', { name: '创建策略' }).click()
  const createDialog = page.getByRole('dialog')
  await expect(
    createDialog.getByRole('heading', { name: '创建策略' }),
  ).toBeVisible()

  await createDialog.getByLabel('策略名称').fill('新策略-1')
  await createDialog.getByLabel('策略模板').selectOption('tpl-ma-cross')
  await createDialog.getByLabel('shortPeriod').fill('7')
  await createDialog.getByLabel('longPeriod').fill('21')
  await createDialog.getByRole('button', { name: '创建策略' }).click()

  await expect(createDialog).toBeHidden()
  await expect(page.getByText('新策略-1')).toBeVisible()

  // 删除保护：409 STRATEGY_IN_USE
  const inUseRow = page.getByRole('row', { name: /占用策略/ })
  await inUseRow.getByRole('button', { name: '删除' }).click()

  const deleteDialog = page.getByRole('dialog')
  await expect(
    deleteDialog.getByRole('heading', { name: '确认删除' }),
  ).toBeVisible()
  await deleteDialog.getByRole('button', { name: '确认删除' }).click()

  await expect(deleteDialog.getByRole('alert')).toContainText('无法删除')
})

test('strategies: wizard create -> detail page', async ({ page }) => {
  await installMockBackend(page)

  await page.goto('/strategies/simple')
  await expect(page.getByRole('heading', { name: '向导式创建策略' })).toBeVisible()

  // Step1: 选择模板
  await page
    .getByRole('button', { name: /均线交叉/ })
    .click({ force: true })

  // Step2: 配置参数
  await page.getByLabel('策略名称').fill('向导策略-1')
  await page.getByLabel('shortPeriod').fill('5')
  await page.getByLabel('longPeriod').fill('20')
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
