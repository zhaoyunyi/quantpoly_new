/**
 * Frontend Entry Wiring — entry-wiring.test.tsx
 *
 * 目标：在应用入口完成：
 * - configureClient(baseUrl) 的统一配置
 * - 全局 Providers（Auth/Toast/ErrorBoundary）
 * - ProtectedLayout（AuthGuard + AppShell）作为受保护页面的标准外壳
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

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

    const mockFetch = vi.fn().mockResolvedValue({
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

    // AppShell 的品牌文案应存在（基础烟测）
    expect(screen.getByText('QuantPoly')).toBeInTheDocument()
  })
})

