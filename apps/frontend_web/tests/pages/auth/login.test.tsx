/**
 * Auth Pages — /auth/login
 *
 * GIVEN: 未登录用户访问登录页
 * WHEN:  提交登录表单
 * THEN:  401 展示错误；成功则跳转 next（或默认 /dashboard）
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AppProviders, bootstrapApiClient } from '../../../app/entry_wiring'

vi.mock('../../../app/lib/navigation', () => ({
  redirectTo: vi.fn(),
}))

describe('/auth/login', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    bootstrapApiClient('http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_invalid_credentials_when_submit_then_shows_error', async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith('/users/me')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: false,
              error: { code: 'UNAUTHORIZED', message: '未认证' },
            }),
        })
      }

      if (url.endsWith('/auth/login')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: false,
              error: { code: 'HTTP_ERROR', message: 'Invalid credentials' },
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/auth/login')

    render(
      <AppProviders>
        <mod.LoginPage />
      </AppProviders>,
    )

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('邮箱'), 'u1@example.com')
    await user.type(screen.getByLabelText('密码'), 'bad-password')
    await user.click(screen.getByRole('button', { name: '登录' }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('邮箱或密码不正确')
    })
  })

  it('given_next_param_when_login_success_then_redirects_to_next', async () => {
    // 让页面能读取到 next query
    window.history.pushState({}, '', '/auth/login?next=%2Fdashboard')

    let meCalls = 0
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith('/users/me')) {
        meCalls += 1
        if (meCalls === 1) {
          return Promise.resolve({
            ok: false,
            status: 401,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: () =>
              Promise.resolve({
                success: false,
                error: { code: 'UNAUTHORIZED', message: '未认证' },
              }),
          })
        }
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

      if (url.endsWith('/auth/login')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'ok',
              data: { token: 't-1' },
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/auth/login')
    const nav = await import('../../../app/lib/navigation')
    const redirectMock = nav.redirectTo as unknown as ReturnType<typeof vi.fn>

    render(
      <AppProviders>
        <mod.LoginPage />
      </AppProviders>,
    )

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('邮箱'), 'u1@example.com')
    await user.type(screen.getByLabelText('密码'), 'good-password')
    await user.click(screen.getByRole('button', { name: '登录' }))

    await waitFor(() => {
      expect(redirectMock).toHaveBeenCalledWith('/dashboard')
    })
  })
})
