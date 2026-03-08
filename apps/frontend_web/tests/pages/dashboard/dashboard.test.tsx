/**
 * Dashboard Page — /dashboard
 *
 * 目标：
 * - summary.degraded.enabled=true 时展示降级提示与原因
 * - 401（未登录）时 AuthGuard 触发跳转到登录页
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { AppProviders, bootstrapApiClient } from '../../../app/entry_wiring'

vi.mock('@qp/shell/redirect', () => ({
  redirectTo: vi.fn(),
}))

describe('/dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    bootstrapApiClient('http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_degraded_summary_when_render_then_shows_banner_and_reasons', async () => {
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
                metadata: { version: 'v2', latencyMs: 10, sources: { accounts: 'degraded' } },
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
                degraded: {
                  enabled: true,
                  reasons: ['accounts_unavailable', 'signals_unavailable'],
                },
                isEmpty: true,
              },
            }),
        })
      }

      if (url.endsWith('/trading/accounts/aggregate')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
                userId: 'u-1',
                accountCount: 0,
                totalCashBalance: 0,
                totalMarketValue: 0,
                totalUnrealizedPnl: 0,
                totalEquity: 0,
                totalTradeCount: 0,
                totalTurnover: 0,
                pendingOrderCount: 0,
              },
            }),
        })
      }

      if (url.endsWith('/backtests/statistics')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: {
                pendingCount: 0,
                runningCount: 0,
                completedCount: 0,
                failedCount: 0,
                cancelledCount: 0,
                totalCount: 0,
                averageReturnRate: 0,
                averageMaxDrawdown: 0,
                averageWinRate: 0,
              },
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })

    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/dashboard')

    render(
      <AppProviders>
        <mod.DashboardPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(([u]) => String(u).endsWith('/monitor/summary')),
      ).toBe(true)
    })

    expect(screen.getByText('部分数据源已降级')).toBeInTheDocument()
    expect(screen.getByText('accounts_unavailable')).toBeInTheDocument()
    expect(screen.getByText('signals_unavailable')).toBeInTheDocument()
  })

  it('given_401_me_when_open_dashboard_then_auth_guard_redirects', async () => {
    window.history.pushState({}, '', '/dashboard?foo=1')

    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith('/users/me')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: false,
              error: { code: 'UNAUTHORIZED', message: 'unauthorized' },
            }),
        })
      }
      throw new Error(`unexpected fetch url: ${url}`)
    })

    vi.stubGlobal('fetch', mockFetch)

    const redirect = await import('@qp/shell/redirect')
    const redirectMock = redirect.redirectTo as unknown as ReturnType<typeof vi.fn>

    const mod = await import('../../../app/routes/dashboard')

    render(
      <AppProviders>
        <mod.DashboardPage />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(redirectMock).toHaveBeenCalledWith(
        '/auth/login?next=%2Fdashboard%3Ffoo%3D1',
      )
    })
  })
})

