/**
 * Monitoring Page — /monitor
 *
 * 目标：
 * - WS signals_update 到达时，列表应更新
 * - WS 断线后进入降级提示
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'

import { AppProviders, bootstrapApiClient } from '../../../app/entry_wiring'

class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  sent: string[] = []

  onopen: (() => void) | null = null
  onmessage: ((event: { data: any }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  open() {
    this.onopen?.()
  }

  send(data: any) {
    this.sent.push(String(data))
  }

  close() {
    this.onclose?.()
  }

  emitJson(obj: any) {
    this.onmessage?.({ data: JSON.stringify(obj) })
  }
}

describe('/monitor', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    bootstrapApiClient('http://localhost:8000')
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket as any)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_ws_signals_update_when_receive_then_list_updates', async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith('/users/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
                id: 'u-1',
                email: 'u1@example.com',
                displayName: 'U1',
                isActive: true,
                emailVerified: true,
                role: 'user',
                level: 1,
              },
            }),
        })
      }

      if (url.endsWith('/monitor/summary')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
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
              },
            }),
        })
      }

      if (url.endsWith('/signals/pending')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: [],
            }),
        })
      }

      if (url.includes('/risk/alerts')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: [],
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
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
          items: [
            {
              id: 'sig-1',
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
            },
          ],
        },
        timestamp: 1,
      })
    })

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
    })
  })

  it('given_ws_disconnect_when_close_then_shows_degraded_badge', async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith('/users/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
                id: 'u-1',
                email: 'u1@example.com',
                displayName: 'U1',
                isActive: true,
                emailVerified: true,
                role: 'user',
                level: 1,
              },
            }),
        })
      }

      if (url.endsWith('/monitor/summary')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
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
              },
            }),
        })
      }

      if (url.endsWith('/signals/pending')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: [],
            }),
        })
      }

      if (url.includes('/risk/alerts')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: [],
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
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
})
