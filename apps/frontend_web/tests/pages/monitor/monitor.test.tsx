/**
 * Monitoring Page — /monitor
 *
 * 目标：
 * - WS signals_update 到达时，列表应更新
 * - WS 断线后进入降级提示
 * - 支持 signals 三类读取与筛选（pending / list / search）
 * - 支持 signals 批量执行/取消
 * - 支持 alerts 统计与批量确认
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AppProviders, bootstrapApiClient } from '../../../app/entry_wiring'

class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  sent: string[] = []

  onopen: (() => void) | null = null
  onmessage: ((event: { data: unknown }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  open() {
    this.onopen?.()
  }

  send(data: unknown) {
    this.sent.push(String(data))
  }

  close() {
    this.onclose?.()
  }

  emitJson(obj: unknown) {
    this.onmessage?.({ data: JSON.stringify(obj) })
  }
}

const DEFAULT_USER = {
  id: 'u-1',
  email: 'u1@example.com',
  displayName: 'U1',
  isActive: true,
  emailVerified: true,
  role: 'user',
  level: 1,
}

const DEFAULT_SUMMARY = {
  type: 'monitor.summary',
  generatedAt: '2026-01-01T00:00:00Z',
  metadata: { version: 'v2', latencyMs: 10, sources: {} },
  accounts: { total: 0, active: 0 },
  strategies: { total: 0, active: 0 },
  backtests: {
    total: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
  },
  tasks: {
    total: 0,
    queued: 0,
    running: 0,
    succeeded: 0,
    failed: 0,
    cancelled: 0,
  },
  signals: { total: 0, pending: 0, expired: 0 },
  alerts: { total: 0, open: 0, critical: 0 },
  degraded: { enabled: false, reasons: [] },
  isEmpty: true,
}

const DEFAULT_ALERT_STATS = {
  total: 0,
  open: 0,
  acknowledged: 0,
  resolved: 0,
  bySeverity: {},
}

function okEnvelope(data: unknown): Response {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: () => Promise.resolve({ success: true, message: 'ok', data }),
  } as unknown as Response
}

function buildSignal(partial?: Partial<Record<string, unknown>>) {
  return {
    id: 'sig-default',
    userId: 'u-1',
    strategyId: 'st-1',
    accountId: 'acc-1',
    symbol: 'AAPL',
    side: 'BUY',
    status: 'pending',
    createdAt: null,
    updatedAt: null,
    expiresAt: null,
    metadata: {},
    ...partial,
  }
}

function buildAlert(partial?: Partial<Record<string, unknown>>) {
  return {
    id: 'alert-default',
    userId: 'u-1',
    accountId: 'acc-1',
    ruleName: 'max-loss',
    severity: 'high',
    message: 'loss breach',
    status: 'open',
    createdAt: null,
    acknowledgedAt: null,
    acknowledgedBy: null,
    resolvedAt: null,
    resolvedBy: null,
    notificationStatus: null,
    notifiedAt: null,
    notifiedBy: null,
    ...partial,
  }
}

interface FetchMockOptions {
  pendingSignals?: unknown[]
  listedSignals?: unknown[]
  searchedSignals?: unknown[]
  alerts?: unknown[]
  alertStats?: unknown
  batchExecuteResult?: unknown
  batchCancelResult?: unknown
  batchAcknowledgeResult?: unknown
}

function createFetchMock(opts: FetchMockOptions = {}) {
  const pendingSignals = opts.pendingSignals ?? []
  const listedSignals = opts.listedSignals ?? []
  const searchedSignals = opts.searchedSignals ?? []
  const alerts = opts.alerts ?? []
  const alertStats = opts.alertStats ?? DEFAULT_ALERT_STATS
  const batchExecuteResult = opts.batchExecuteResult ?? {
    total: 0,
    executed: 0,
    skipped: 0,
    denied: 0,
    results: [],
    idempotent: false,
  }
  const batchCancelResult = opts.batchCancelResult ?? {
    total: 0,
    cancelled: 0,
    skipped: 0,
    denied: 0,
    results: [],
    idempotent: false,
  }
  const batchAcknowledgeResult = opts.batchAcknowledgeResult ?? { affected: 0 }

  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const method = String(init?.method ?? 'GET').toUpperCase()

    if (url.endsWith('/users/me')) return Promise.resolve(okEnvelope(DEFAULT_USER))
    if (url.endsWith('/monitor/summary')) return Promise.resolve(okEnvelope(DEFAULT_SUMMARY))

    if (url.includes('/risk/alerts/stats')) return Promise.resolve(okEnvelope(alertStats))
    if (method === 'POST' && url.endsWith('/risk/alerts/batch-acknowledge')) {
      return Promise.resolve(okEnvelope(batchAcknowledgeResult))
    }
    if (method === 'GET' && url.includes('/risk/alerts')) return Promise.resolve(okEnvelope(alerts))

    if (method === 'POST' && url.endsWith('/signals/batch/execute')) {
      return Promise.resolve(okEnvelope(batchExecuteResult))
    }
    if (method === 'POST' && url.endsWith('/signals/batch/cancel')) {
      return Promise.resolve(okEnvelope(batchCancelResult))
    }
    if (url.includes('/signals/search')) return Promise.resolve(okEnvelope(searchedSignals))
    if (url.includes('/signals?') || url.endsWith('/signals')) {
      return Promise.resolve(okEnvelope(listedSignals))
    }
    if (url.endsWith('/signals/pending')) return Promise.resolve(okEnvelope(pendingSignals))

    if (method === 'POST' && /\/signals\/[^/]+\/process$/.test(url)) {
      return Promise.resolve(okEnvelope(buildSignal({ id: url.split('/').slice(-2)[0] })))
    }
    if (method === 'POST' && /\/signals\/[^/]+\/execute$/.test(url)) {
      return Promise.resolve(okEnvelope(buildSignal({ id: url.split('/').slice(-2)[0] })))
    }
    if (method === 'POST' && /\/signals\/[^/]+\/cancel$/.test(url)) {
      return Promise.resolve(okEnvelope(buildSignal({ id: url.split('/').slice(-2)[0] })))
    }
    if (method === 'PATCH' && /\/risk\/alerts\/[^/]+\/acknowledge$/.test(url)) {
      return Promise.resolve(okEnvelope(buildAlert({ id: url.split('/').slice(-2)[0] })))
    }
    if (method === 'POST' && /\/risk\/alerts\/[^/]+\/resolve$/.test(url)) {
      return Promise.resolve(okEnvelope({ resolved: true }))
    }

    throw new Error(`unexpected fetch request: [${method}] ${url}`)
  })
}

describe('/monitor', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    bootstrapApiClient('http://localhost:8000')
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_ws_signals_update_when_receive_then_list_updates', async () => {
    const mockFetch = createFetchMock()
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/monitor')

    render(
      <AppProviders>
        <mod.MonitorPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1)
    })

    act(() => {
      MockWebSocket.instances[0].open()
      MockWebSocket.instances[0].emitJson({
        type: 'signals_update',
        payload: { snapshot: true, truncated: false, counts: { total: 1, pending: 1, expired: 0 } },
        data: {
          items: [buildSignal({ id: 'sig-1', symbol: 'AAPL' })],
        },
        timestamp: 1,
      })
    })

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
    })
  })

  it('given_ws_disconnect_when_close_then_shows_degraded_badge', async () => {
    const mockFetch = createFetchMock()
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/monitor')

    render(
      <AppProviders>
        <mod.MonitorPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1)
    })

    act(() => {
      MockWebSocket.instances[0].close()
    })

    await waitFor(() => {
      expect(screen.getByText('已降级')).toBeInTheDocument()
    })
  })

  it('given_signal_source_and_filters_when_switch_then_calls_list_and_search_endpoints', async () => {
    const mockFetch = createFetchMock({
      pendingSignals: [buildSignal({ id: 'sig-pending', symbol: 'AAPL' })],
      listedSignals: [buildSignal({ id: 'sig-list', symbol: 'MSFT' })],
      searchedSignals: [buildSignal({ id: 'sig-search', symbol: 'TSLA' })],
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/monitor')
    const user = userEvent.setup()

    render(
      <AppProviders>
        <mod.MonitorPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: '全部信号' }))
    await user.clear(screen.getByLabelText('关键词'))
    await user.type(screen.getByLabelText('关键词'), 'mean')
    await user.click(screen.getByRole('button', { name: '应用筛选' }))

    await waitFor(() => {
      expect(screen.getByText('MSFT')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: '搜索信号' }))
    await user.click(screen.getByRole('button', { name: '应用筛选' }))

    await waitFor(() => {
      expect(screen.getByText('TSLA')).toBeInTheDocument()
    })

    expect(mockFetch.mock.calls.some(([u]) => String(u).includes('/signals?'))).toBe(true)
    expect(mockFetch.mock.calls.some(([u]) => String(u).includes('/signals/search'))).toBe(true)
  })

  it('given_signal_selection_when_batch_actions_then_calls_execute_and_cancel_endpoints', async () => {
    const mockFetch = createFetchMock({
      pendingSignals: [
        buildSignal({ id: 'sig-1', symbol: 'AAPL' }),
        buildSignal({ id: 'sig-2', symbol: 'TSLA' }),
      ],
      batchExecuteResult: {
        total: 2,
        executed: 2,
        skipped: 0,
        denied: 0,
        results: [],
        idempotent: false,
      },
      batchCancelResult: {
        total: 2,
        cancelled: 2,
        skipped: 0,
        denied: 0,
        results: [],
        idempotent: false,
      },
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/monitor')
    const user = userEvent.setup()

    render(
      <AppProviders>
        <mod.MonitorPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
      expect(screen.getByText('TSLA')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('checkbox', { name: '选择全部信号' }))
    await user.click(screen.getByRole('button', { name: '批量执行' }))

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, init]) =>
            String(u).endsWith('/signals/batch/execute') &&
            String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
        ),
      ).toBe(true)
    })

    const executeCall = mockFetch.mock.calls.find(
      ([u, init]) =>
        String(u).endsWith('/signals/batch/execute') &&
        String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
    )
    expect(executeCall).toBeTruthy()
    const executeBody = JSON.parse(
      String((executeCall?.[1] as RequestInit | undefined)?.body ?? '{}'),
    ) as { signalIds?: string[] }
    expect(executeBody.signalIds).toEqual(['sig-1', 'sig-2'])

    await user.click(screen.getByRole('checkbox', { name: '选择全部信号' }))
    await user.click(screen.getByRole('button', { name: '批量取消' }))

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, init]) =>
            String(u).endsWith('/signals/batch/cancel') &&
            String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
        ),
      ).toBe(true)
    })

    const cancelCall = mockFetch.mock.calls.find(
      ([u, init]) =>
        String(u).endsWith('/signals/batch/cancel') &&
        String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
    )
    expect(cancelCall).toBeTruthy()
    const cancelBody = JSON.parse(
      String((cancelCall?.[1] as RequestInit | undefined)?.body ?? '{}'),
    ) as { signalIds?: string[] }
    expect(cancelBody.signalIds).toEqual(['sig-1', 'sig-2'])
  })

  it('given_alert_stats_and_selection_when_batch_ack_then_calls_stats_and_batch_acknowledge', async () => {
    const mockFetch = createFetchMock({
      alerts: [
        buildAlert({ id: 'alert-1', ruleName: '仓位集中度', severity: 'critical' }),
        buildAlert({ id: 'alert-2', ruleName: '最大回撤', severity: 'high' }),
      ],
      alertStats: {
        total: 17,
        open: 5,
        acknowledged: 7,
        resolved: 5,
        bySeverity: { critical: 2, high: 4 },
      },
      batchAcknowledgeResult: { affected: 2 },
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/monitor')
    const user = userEvent.setup()

    render(
      <AppProviders>
        <mod.MonitorPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText('告警总量')).toBeInTheDocument()
      expect(screen.getByText('17')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('checkbox', { name: '选择全部告警' }))
    await user.click(screen.getByRole('button', { name: '批量确认告警' }))

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, init]) =>
            String(u).endsWith('/risk/alerts/batch-acknowledge') &&
            String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
        ),
      ).toBe(true)
    })

    const batchAckCall = mockFetch.mock.calls.find(
      ([u, init]) =>
        String(u).endsWith('/risk/alerts/batch-acknowledge') &&
        String((init as RequestInit | undefined)?.method ?? 'GET').toUpperCase() === 'POST',
    )
    expect(batchAckCall).toBeTruthy()
    const batchAckBody = JSON.parse(
      String((batchAckCall?.[1] as RequestInit | undefined)?.body ?? '{}'),
    ) as { alertIds?: string[] }
    expect(batchAckBody.alertIds).toEqual(['alert-1', 'alert-2'])

    expect(mockFetch.mock.calls.some(([u]) => String(u).includes('/risk/alerts/stats'))).toBe(true)
  })
})
