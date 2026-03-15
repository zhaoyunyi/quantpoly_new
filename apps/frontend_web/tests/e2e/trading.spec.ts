import { test, expect, type Page, type Request } from '@playwright/test'

type OrderSide = 'BUY' | 'SELL'
type OrderStatus = 'pending' | 'filled' | 'cancelled' | 'failed'

interface TradingAccount {
  id: string
  userId: string
  accountName: string
  isActive: boolean
  createdAt: string
}

interface Position {
  id: string
  userId: string
  accountId: string
  symbol: string
  quantity: number
  avgPrice: number
  lastPrice: number
}

interface TradeOrder {
  id: string
  userId: string
  accountId: string
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  status: OrderStatus
  createdAt: string
  updatedAt: string
}

interface TradeRecord {
  id: string
  userId: string
  accountId: string
  orderId: string | null
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  createdAt: string
}

type CashFlowType = 'deposit' | 'withdraw' | 'trade_buy' | 'trade_sell'

interface CashFlow {
  id: string
  userId: string
  accountId: string
  amount: number
  flowType: CashFlowType
  relatedTradeId: string | null
  createdAt: string
}

interface CashFlowSummary {
  flowCount: number
  totalInflow: number
  totalOutflow: number
  netFlow: number
  latestFlowAt: string | null
}

interface AccountOverview {
  positionCount: number
  totalMarketValue: number
  unrealizedPnl: number
  tradeCount: number
  turnover: number
  orderCount: number
  pendingOrderCount: number
  filledOrderCount: number
  cancelledOrderCount: number
  failedOrderCount: number
  cashBalance: number
}

interface RiskMetrics {
  accountId: string
  riskScore: number
  riskLevel: 'low' | 'medium' | 'high'
  exposureRatio: number
  leverage: number
  unrealizedPnl: number
  pendingOrderCount: number
  evaluatedAt: string
}

interface EquityCurvePoint {
  timestamp: string
  cashBalance: number
  marketValue: number
  equity: number
}

interface TradeStats {
  tradeCount: number
  turnover: number
}

interface RiskAssessment {
  assessmentId: string
  accountId: string
  strategyId: string | null
  riskScore: number
  riskLevel: string
  triggeredRuleIds: string[]
  createdAt: string
}

interface RangeStats {
  min: number
  max: number
  average: number
}

interface AccountFilterConfig {
  totalAccounts: number
  totalAssets: RangeStats | null
  profitLoss: RangeStats | null
  profitLossRate: RangeStats | null
  accountTypeCounts: Record<string, number>
  statusCounts: Record<string, number>
  riskLevelCounts: Record<string, number>
  hasPositionsCount: number
  hasFrozenBalanceCount: number
}

interface TradingAccountsAggregate {
  userId: string
  accountCount: number
  totalCashBalance: number
  totalMarketValue: number
  totalUnrealizedPnl: number
  totalEquity: number
  totalTradeCount: number
  totalTurnover: number
  pendingOrderCount: number
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

function rangeStats(values: number[]): RangeStats | null {
  if (values.length === 0) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  const average = values.reduce((a, b) => a + b, 0) / values.length
  return { min, max, average }
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

  let nextAccountSeq = 2
  let nextOrderSeq = 1
  let nextTradeSeq = 1
  let nextCashFlowSeq = 1
  let nextRiskSeq = 1

  const accounts: TradingAccount[] = [
    {
      id: 'acc-1',
      userId: me.id,
      accountName: '主账户',
      isActive: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
  ]

  const cashBalance = new Map<string, number>([['acc-1', 10_000]])
  const tradeStats = new Map<string, TradeStats>([['acc-1', { tradeCount: 0, turnover: 0 }]])

  const positionsByAccount = new Map<string, Position[]>([
    [
      'acc-1',
      [
        {
          id: 'pos-1',
          userId: me.id,
          accountId: 'acc-1',
          symbol: 'AAPL',
          quantity: 100,
          avgPrice: 150,
          lastPrice: 160,
        },
      ],
    ],
  ])

  const ordersByAccount = new Map<string, TradeOrder[]>([
    [
      'acc-1',
      [
        {
          id: 'ord-pending-1',
          userId: me.id,
          accountId: 'acc-1',
          symbol: 'AAPL',
          side: 'BUY',
          quantity: 1,
          price: 160,
          status: 'pending',
          createdAt: '2026-01-10T00:00:00Z',
          updatedAt: '2026-01-10T00:00:00Z',
        },
      ],
    ],
  ])

  const cashFlowsByAccount = new Map<string, CashFlow[]>([
    [
      'acc-1',
      [
        {
          id: `cf-${nextCashFlowSeq++}`,
          userId: me.id,
          accountId: 'acc-1',
          amount: 10_000,
          flowType: 'deposit',
          relatedTradeId: null,
          createdAt: '2026-01-01T00:00:00Z',
        },
      ],
    ],
  ])

  const riskAssessmentByAccount = new Map<string, RiskAssessment | null>([
    ['acc-1', null],
  ])

  function getAccountOrThrow(accountId: string): TradingAccount {
    const acc = accounts.find((a) => a.id === accountId)
    if (!acc) throw new Error(`account not found: ${accountId}`)
    return acc
  }

  function getPositions(accountId: string): Position[] {
    return positionsByAccount.get(accountId) ?? []
  }

  function getOrders(accountId: string): TradeOrder[] {
    return ordersByAccount.get(accountId) ?? []
  }

  function setOrders(accountId: string, orders: TradeOrder[]) {
    ordersByAccount.set(accountId, orders)
  }

  function pushCashFlow(accountId: string, flow: CashFlow) {
    const flows = cashFlowsByAccount.get(accountId) ?? []
    flows.unshift(flow)
    cashFlowsByAccount.set(accountId, flows)
  }

  function computePositionMetrics(accountId: string) {
    const positions = getPositions(accountId)
    const totalMarketValue = positions.reduce((s, p) => s + p.quantity * p.lastPrice, 0)
    const totalCost = positions.reduce((s, p) => s + p.quantity * p.avgPrice, 0)
    return {
      positionCount: positions.length,
      totalMarketValue,
      unrealizedPnl: totalMarketValue - totalCost,
      totalCost,
    }
  }

  function computeOverview(accountId: string): AccountOverview {
    getAccountOrThrow(accountId)
    const { positionCount, totalMarketValue, unrealizedPnl } = computePositionMetrics(accountId)
    const orders = getOrders(accountId)
    const stats = tradeStats.get(accountId) ?? { tradeCount: 0, turnover: 0 }
    const counts = {
      pendingOrderCount: 0,
      filledOrderCount: 0,
      cancelledOrderCount: 0,
      failedOrderCount: 0,
    }
    for (const o of orders) {
      if (o.status === 'pending') counts.pendingOrderCount += 1
      if (o.status === 'filled') counts.filledOrderCount += 1
      if (o.status === 'cancelled') counts.cancelledOrderCount += 1
      if (o.status === 'failed') counts.failedOrderCount += 1
    }
    return {
      positionCount,
      totalMarketValue,
      unrealizedPnl,
      tradeCount: stats.tradeCount,
      turnover: stats.turnover,
      orderCount: orders.length,
      ...counts,
      cashBalance: cashBalance.get(accountId) ?? 0,
    }
  }

  function computeAggregate(): TradingAccountsAggregate {
    let totalCashBalance = 0
    let totalMarketValue = 0
    let totalUnrealizedPnl = 0
    let totalTradeCount = 0
    let totalTurnover = 0
    let pendingOrderCount = 0

    for (const acc of accounts) {
      const overview = computeOverview(acc.id)
      totalCashBalance += overview.cashBalance
      totalMarketValue += overview.totalMarketValue
      totalUnrealizedPnl += overview.unrealizedPnl
      totalTradeCount += overview.tradeCount
      totalTurnover += overview.turnover
      pendingOrderCount += overview.pendingOrderCount
    }

    return {
      userId: me.id,
      accountCount: accounts.length,
      totalCashBalance,
      totalMarketValue,
      totalUnrealizedPnl,
      totalEquity: totalCashBalance + totalMarketValue,
      totalTradeCount,
      totalTurnover,
      pendingOrderCount,
    }
  }

  function computeFilterConfig(): AccountFilterConfig {
    const totalAssetsValues: number[] = []
    const profitLossValues: number[] = []
    const profitLossRateValues: number[] = []
    const statusCounts: Record<string, number> = { active: 0, inactive: 0 }
    const riskLevelCounts: Record<string, number> = { LOW: 0, MEDIUM: 0, HIGH: 0, UNKNOWN: 0 }
    let hasPositionsCount = 0

    for (const acc of accounts) {
      const ov = computeOverview(acc.id)
      const totalAssets = ov.cashBalance + ov.totalMarketValue
      totalAssetsValues.push(totalAssets)
      profitLossValues.push(ov.unrealizedPnl)
      const pnlRate = ov.totalMarketValue > 0 ? ov.unrealizedPnl / ov.totalMarketValue : 0
      profitLossRateValues.push(pnlRate)

      if (ov.positionCount > 0) hasPositionsCount += 1
      statusCounts[acc.isActive ? 'active' : 'inactive'] += 1

      const level = mockRiskMetrics(acc.id).riskLevel.toUpperCase()
      riskLevelCounts[level] = (riskLevelCounts[level] ?? 0) + 1
    }

    return {
      totalAccounts: accounts.length,
      totalAssets: rangeStats(totalAssetsValues),
      profitLoss: rangeStats(profitLossValues),
      profitLossRate: rangeStats(profitLossRateValues),
      accountTypeCounts: { paper: accounts.length },
      statusCounts,
      riskLevelCounts,
      hasPositionsCount,
      hasFrozenBalanceCount: 0,
    }
  }

  function mockRiskMetrics(accountId: string): RiskMetrics {
    const ov = computeOverview(accountId)
    const totalEquity = ov.cashBalance + ov.totalMarketValue
    const exposureRatio = totalEquity > 0 ? ov.totalMarketValue / totalEquity : 0
    const leverage = exposureRatio
    const riskScore = Math.min(100, Math.round(exposureRatio * 60 + (ov.pendingOrderCount > 0 ? 10 : 0)))
    const riskLevel = riskScore >= 70 ? 'high' : riskScore >= 30 ? 'medium' : 'low'
    return {
      accountId,
      riskScore,
      riskLevel,
      exposureRatio: Number(exposureRatio.toFixed(6)),
      leverage: Number(leverage.toFixed(6)),
      unrealizedPnl: ov.unrealizedPnl,
      pendingOrderCount: ov.pendingOrderCount,
      evaluatedAt: nowIso(),
    }
  }

  function mockEquityCurve(accountId: string): EquityCurvePoint[] {
    const ov = computeOverview(accountId)
    const now = Date.now()
    const points: EquityCurvePoint[] = []
    for (let i = 9; i >= 0; i--) {
      const ts = new Date(now - i * 24 * 60 * 60 * 1000).toISOString()
      points.push({
        timestamp: ts,
        cashBalance: ov.cashBalance,
        marketValue: ov.totalMarketValue,
        equity: ov.cashBalance + ov.totalMarketValue,
      })
    }
    return points
  }

  function mockCashFlowSummary(accountId: string): CashFlowSummary {
    const flows = cashFlowsByAccount.get(accountId) ?? []
    const totalInflow = flows.filter((f) => f.amount > 0).reduce((s, f) => s + f.amount, 0)
    const totalOutflow = flows.filter((f) => f.amount < 0).reduce((s, f) => s + -f.amount, 0)
    const latest = flows.length > 0 ? flows[0]?.createdAt ?? null : null
    return {
      flowCount: flows.length,
      totalInflow,
      totalOutflow,
      netFlow: totalInflow - totalOutflow,
      latestFlowAt: latest,
    }
  }

  function executeTradeCommand(accountId: string, side: OrderSide, payload: { symbol: string; quantity: number; price: number }) {
    const { symbol, quantity, price } = payload
    getAccountOrThrow(accountId)

    const cost = quantity * price
    const currentCash = cashBalance.get(accountId) ?? 0
    const positions = [...getPositions(accountId)]
    const orders = [...getOrders(accountId)]

    if (side === 'BUY') {
      if (currentCash < cost) {
        return { status: 409, body: failure('INSUFFICIENT_FUNDS', 'insufficient funds') }
      }
      cashBalance.set(accountId, currentCash - cost)
      const existing = positions.find((p) => p.symbol === symbol)
      if (existing) {
        const newQty = existing.quantity + quantity
        existing.avgPrice = (existing.avgPrice * existing.quantity + price * quantity) / newQty
        existing.quantity = newQty
        existing.lastPrice = price
      } else {
        positions.push({
          id: `pos-${symbol}`,
          userId: me.id,
          accountId,
          symbol,
          quantity,
          avgPrice: price,
          lastPrice: price,
        })
      }
    } else {
      const existing = positions.find((p) => p.symbol === symbol)
      if (!existing || existing.quantity < quantity) {
        return { status: 409, body: failure('INSUFFICIENT_POSITION', 'insufficient position') }
      }
      cashBalance.set(accountId, currentCash + cost)
      existing.quantity -= quantity
      existing.lastPrice = price
      if (existing.quantity <= 0) {
        const idx = positions.indexOf(existing)
        if (idx >= 0) positions.splice(idx, 1)
      }
    }

    const ts = nowIso()
    const order: TradeOrder = {
      id: `ord-${nextOrderSeq++}`,
      userId: me.id,
      accountId,
      symbol,
      side,
      quantity,
      price,
      status: 'filled',
      createdAt: ts,
      updatedAt: ts,
    }
    orders.unshift(order)
    setOrders(accountId, orders)
    positionsByAccount.set(accountId, positions)

    const trade: TradeRecord = {
      id: `tr-${nextTradeSeq++}`,
      userId: me.id,
      accountId,
      orderId: order.id,
      symbol,
      side,
      quantity,
      price,
      createdAt: ts,
    }

    const flow: CashFlow = {
      id: `cf-${nextCashFlowSeq++}`,
      userId: me.id,
      accountId,
      amount: side === 'BUY' ? -cost : cost,
      flowType: side === 'BUY' ? 'trade_buy' : 'trade_sell',
      relatedTradeId: trade.id,
      createdAt: ts,
    }
    pushCashFlow(accountId, flow)

    const stats = tradeStats.get(accountId) ?? { tradeCount: 0, turnover: 0 }
    stats.tradeCount += 1
    stats.turnover += cost
    tradeStats.set(accountId, stats)

    const position = positionsByAccount.get(accountId)?.find((p) => p.symbol === symbol) ?? positions[0]!
    return { status: 200, body: success({ order, trade, cashFlow: flow, position }) }
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

    // GET /trading/accounts
    if (method === 'GET' && url.pathname === '/trading/accounts') {
      return { status: 200, body: success(accounts) }
    }

    // POST /trading/accounts
    if (method === 'POST' && url.pathname === '/trading/accounts') {
      const payload = req.postDataJSON() as { accountName: string; initialCapital?: number }
      const ts = nowIso()
      const created: TradingAccount = {
        id: `acc-${nextAccountSeq++}`,
        userId: me.id,
        accountName: payload.accountName ?? `账户-${nextAccountSeq}`,
        isActive: true,
        createdAt: ts,
      }
      accounts.unshift(created)
      cashBalance.set(created.id, payload.initialCapital ?? 0)
      tradeStats.set(created.id, { tradeCount: 0, turnover: 0 })
      positionsByAccount.set(created.id, [])
      ordersByAccount.set(created.id, [])
      cashFlowsByAccount.set(created.id, [])
      if ((payload.initialCapital ?? 0) > 0) {
        pushCashFlow(created.id, {
          id: `cf-${nextCashFlowSeq++}`,
          userId: me.id,
          accountId: created.id,
          amount: payload.initialCapital ?? 0,
          flowType: 'deposit',
          relatedTradeId: null,
          createdAt: ts,
        })
      }
      riskAssessmentByAccount.set(created.id, null)
      return { status: 200, body: success(created) }
    }

    // GET /trading/accounts/aggregate
    if (method === 'GET' && url.pathname === '/trading/accounts/aggregate') {
      return { status: 200, body: success(computeAggregate()) }
    }

    // GET /trading/accounts/filter-config
    if (method === 'GET' && url.pathname === '/trading/accounts/filter-config') {
      return { status: 200, body: success(computeFilterConfig()) }
    }

    // /trading/accounts/:id/...
    if (parts.length >= 2 && parts[0] === 'trading' && parts[1] === 'accounts') {
      const accountId = decodeURIComponent(parts[2] ?? '')

      // PUT /trading/accounts/:id
      if (parts.length === 3 && method === 'PUT') {
        const payload = req.postDataJSON() as { accountName?: string; isActive?: boolean }
        const acc = getAccountOrThrow(accountId)
        acc.accountName = payload.accountName ?? acc.accountName
        acc.isActive = payload.isActive ?? acc.isActive
        return { status: 200, body: success(acc) }
      }

      // GET /trading/accounts/:id/overview
      if (parts.length === 4 && parts[3] === 'overview' && method === 'GET') {
        return { status: 200, body: success(computeOverview(accountId)) }
      }

      // GET /trading/accounts/:id/positions
      if (parts.length === 4 && parts[3] === 'positions' && method === 'GET') {
        return { status: 200, body: success(getPositions(accountId)) }
      }

      // GET /trading/accounts/:id/orders
      if (parts.length === 4 && parts[3] === 'orders' && method === 'GET') {
        return { status: 200, body: success(getOrders(accountId)) }
      }

      // POST /trading/accounts/:id/orders/:orderId/cancel
      if (parts.length === 6 && parts[3] === 'orders' && parts[5] === 'cancel' && method === 'POST') {
        const orderId = decodeURIComponent(parts[4] ?? '')
        const orders = getOrders(accountId)
        const order = orders.find((o) => o.id === orderId)
        if (!order) return { status: 404, body: failure('ORDER_NOT_FOUND', 'order not found') }
        order.status = 'cancelled'
        order.updatedAt = nowIso()
        return { status: 200, body: success(order) }
      }

      // POST /trading/accounts/:id/buy
      if (parts.length === 4 && parts[3] === 'buy' && method === 'POST') {
        const payload = req.postDataJSON() as { symbol: string; quantity: number; price: number }
        return executeTradeCommand(accountId, 'BUY', payload)
      }

      // POST /trading/accounts/:id/sell
      if (parts.length === 4 && parts[3] === 'sell' && method === 'POST') {
        const payload = req.postDataJSON() as { symbol: string; quantity: number; price: number }
        return executeTradeCommand(accountId, 'SELL', payload)
      }

      // GET /trading/accounts/:id/cash-flows
      if (parts.length === 4 && parts[3] === 'cash-flows' && method === 'GET') {
        return { status: 200, body: success(cashFlowsByAccount.get(accountId) ?? []) }
      }

      // GET /trading/accounts/:id/cash-flows/summary
      if (parts.length === 5 && parts[3] === 'cash-flows' && parts[4] === 'summary' && method === 'GET') {
        return { status: 200, body: success(mockCashFlowSummary(accountId)) }
      }

      // POST /trading/accounts/:id/deposit
      if (parts.length === 4 && parts[3] === 'deposit' && method === 'POST') {
        const payload = req.postDataJSON() as { amount: number }
        const amt = Number(payload.amount ?? 0)
        cashBalance.set(accountId, (cashBalance.get(accountId) ?? 0) + amt)
        const flow: CashFlow = {
          id: `cf-${nextCashFlowSeq++}`,
          userId: me.id,
          accountId,
          amount: amt,
          flowType: 'deposit',
          relatedTradeId: null,
          createdAt: nowIso(),
        }
        pushCashFlow(accountId, flow)
        return { status: 200, body: success(flow) }
      }

      // POST /trading/accounts/:id/withdraw
      if (parts.length === 4 && parts[3] === 'withdraw' && method === 'POST') {
        const payload = req.postDataJSON() as { amount: number }
        const amt = Number(payload.amount ?? 0)
        const currentCash = cashBalance.get(accountId) ?? 0
        if (currentCash < amt) return { status: 409, body: failure('INSUFFICIENT_FUNDS', 'insufficient funds') }
        cashBalance.set(accountId, currentCash - amt)
        const flow: CashFlow = {
          id: `cf-${nextCashFlowSeq++}`,
          userId: me.id,
          accountId,
          amount: -amt,
          flowType: 'withdraw',
          relatedTradeId: null,
          createdAt: nowIso(),
        }
        pushCashFlow(accountId, flow)
        return { status: 200, body: success(flow) }
      }

      // GET /trading/accounts/:id/risk-metrics
      if (parts.length === 4 && parts[3] === 'risk-metrics' && method === 'GET') {
        return { status: 200, body: success(mockRiskMetrics(accountId)) }
      }

      // GET /trading/accounts/:id/equity-curve
      if (parts.length === 4 && parts[3] === 'equity-curve' && method === 'GET') {
        return { status: 200, body: success(mockEquityCurve(accountId)) }
      }

      // GET /trading/accounts/:id/trade-stats
      if (parts.length === 4 && parts[3] === 'trade-stats' && method === 'GET') {
        return { status: 200, body: success(tradeStats.get(accountId) ?? { tradeCount: 0, turnover: 0 }) }
      }

      // GET /trading/accounts/:id/risk-assessment
      if (parts.length === 4 && parts[3] === 'risk-assessment' && method === 'GET') {
        const ra = riskAssessmentByAccount.get(accountId)
        if (!ra) return { status: 202, body: failure('RISK_ASSESSMENT_PENDING', 'risk assessment pending') }
        return { status: 200, body: success(ra) }
      }

      // POST /trading/accounts/:id/risk-assessment/evaluate
      if (parts.length === 5 && parts[3] === 'risk-assessment' && parts[4] === 'evaluate' && method === 'POST') {
        const snapshot: RiskAssessment = {
          assessmentId: `ra-${nextRiskSeq++}`,
          accountId,
          strategyId: null,
          riskScore: 40,
          riskLevel: 'medium',
          triggeredRuleIds: ['rule-1'],
          createdAt: nowIso(),
        }
        riskAssessmentByAccount.set(accountId, snapshot)
        return { status: 200, body: success(snapshot) }
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

test('trading: buy/sell error mapping', async ({ page }) => {
  await installMockBackend(page)

  await page.goto('/trading')

  await expect(
    page.getByRole('heading', { name: '交易', exact: true }),
  ).toBeVisible()

  // 选择账户
  await page.getByRole('combobox', { name: '交易账户' }).click()
  await page.getByText('主账户').click()

  // 买入资金不足
  await page.getByLabel('标的代码').fill('AAPL')
  await page.getByLabel('数量').fill('1000')
  await page.getByLabel('价格').fill('1000')
  await page.getByRole('button', { name: '确认买入' }).click()
  await expect(
    page.getByText('可用资金不足，无法完成买入。请存入资金后重试。'),
  ).toBeVisible()

  // 卖出持仓不足
  await page.getByRole('button', { name: '卖出' }).click()
  await page.getByLabel('标的代码').fill('AAPL')
  await page.getByLabel('数量').fill('1000')
  await page.getByLabel('价格').fill('100')
  await page.getByRole('button', { name: '确认卖出' }).click()
  await expect(
    page.getByText('可用持仓不足，无法完成卖出。请确认持仓数量。'),
  ).toBeVisible()
})

test('trading: analytics pending -> evaluate', async ({ page }) => {
  await installMockBackend(page)

  await page.goto('/trading/analytics')

  await expect(page.getByRole('heading', { name: '分析报表' })).toBeVisible()

  await page.getByRole('combobox', { name: '交易账户' }).click()
  await page.getByText('主账户').click()

  await expect(
    page.getByText('风险评估快照正在生成中，请稍后刷新查看结果。'),
  ).toBeVisible()

  await page.getByRole('button', { name: '发起评估' }).click()
  await expect(page.getByText('评估 ID')).toBeVisible()
})

test('trading: accounts page loads filter config and can create account', async ({ page }) => {
  await installMockBackend(page)

  await page.goto('/trading/accounts')

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
