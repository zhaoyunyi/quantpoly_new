/**
 * Frontend Entry Wiring — entry-wiring.test.tsx
 *
 * 目标：在应用入口完成：
 * - configureClient(baseUrl) 的统一配置
 * - 全局 Providers（Auth/Toast/ErrorBoundary）
 * - ProtectedLayout（AuthGuard + AppShell）作为受保护页面的标准外壳
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'

describe('entry_wiring', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_backend_origin_when_normalized_then_trims_and_removes_trailing_slash', async () => {
    const mod = await import('../../app/routes/__root')

    expect(typeof mod.normalizeBackendOrigin).toBe('function')
    expect(mod.normalizeBackendOrigin('  http://localhost:8000/  ')).toBe(
      'http://localhost:8000',
    )
  })

  it('given_origin_when_bootstrap_then_configures_api_client_base_url', async () => {
    const root = await import('../../app/routes/__root')
    const api = await import('@qp/api-client')

    expect(typeof root.bootstrapApiClient).toBe('function')

    root.bootstrapApiClient('http://example.test/')
    expect(api.getClientConfig().baseUrl).toBe('http://example.test')
  })

  it('given_authenticated_me_when_render_protected_layout_then_renders_shell_and_children', async () => {
    const root = await import('../../app/routes/__root')

    expect(typeof root.AppProviders).toBe('function')
    expect(typeof root.ProtectedLayout).toBe('function')

    // 配置 API client（避免 request() 的 baseUrl 为空）
    root.bootstrapApiClient('http://localhost:8000')

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
      if (url.endsWith('/health')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: { status: 'healthy', enabledContexts: ['user_auth'] },
            }),
        })
      }
      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    render(
      <root.AppProviders>
        <root.ProtectedLayout>
          <div>secret</div>
        </root.ProtectedLayout>
      </root.AppProviders>,
    )

    // 初始应先显示验证中状态（AuthGuard loading）
    expect(screen.getByText('正在验证身份…')).toBeInTheDocument()

    // refresh 完成后应能渲染 AppShell 与 children
    await waitFor(() => {
      expect(screen.getByText('secret')).toBeInTheDocument()
    })

    // 服务状态可见，且全页只出现一次
    const serviceRunning = await screen.findByText('服务运行中')
    expect(serviceRunning).toBeInTheDocument()
    expect(screen.getAllByText('服务运行中')).toHaveLength(1)

    // 左侧导航栏恢复，且不应出现顶部横向菜单导致的重复链接
    expect(screen.getByText('QuantPoly')).toBeInTheDocument()
    const collapseButton = screen.getByLabelText('收起侧栏')
    expect(collapseButton).toBeInTheDocument()
    const sidebarHeader = screen.getByTestId('shell-sidebar-header')
    expect(sidebarHeader).toHaveClass('justify-between')
    expect(
      within(collapseButton).getByTestId('shell-sidebar-toggle-icon'),
    ).toHaveAttribute('data-icon', 'collapse-sidebar')
    expect(screen.getByRole('link', { name: '仪表盘' })).toHaveAttribute(
      'href',
      '/dashboard',
    )
    expect(screen.getByRole('link', { name: '策略管理' })).toHaveAttribute(
      'href',
      '/strategies',
    )
    expect(screen.getAllByRole('link', { name: '仪表盘' })).toHaveLength(1)
    expect(screen.getAllByRole('link', { name: '策略管理' })).toHaveLength(1)

    // 顶部横向导航栏已移除（不再包含菜单链接）
    const topNav = screen.queryByTestId('shell-top-nav')
    if (topNav) {
      expect(within(topNav).queryAllByRole('link')).toHaveLength(0)
    }
  })
})
