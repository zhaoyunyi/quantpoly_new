/**
 * Auth Pages — Password Reset Flow
 *
 * GIVEN: 用户忘记密码 / 拿到 reset token
 * WHEN:  发起重置请求 / 提交新密码
 * THEN:  始终返回非枚举成功语义；token 无效时提示失败；成功时提示重新登录
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AppProviders, bootstrapApiClient } from '../../../app/entry_wiring'

describe('password_reset_flow', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    bootstrapApiClient('http://localhost:8000')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('given_email_when_request_reset_then_shows_non_enumerating_success', async () => {
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

      if (url.endsWith('/auth/password-reset/request')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message:
                'If the account exists, password reset instructions have been sent',
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/auth/forgot-password')

    render(
      <AppProviders>
        <mod.ForgotPasswordPage />
      </AppProviders>,
    )

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('邮箱'), 'u1@example.com')
    await user.click(screen.getByRole('button', { name: '发送重置指引' }))

    await waitFor(() => {
      expect(
        screen.getByText('如果该账户存在，我们已发送重置指引。'),
      ).toBeInTheDocument()
    })
  })

  it('given_token_in_query_when_confirm_with_invalid_token_then_shows_error', async () => {
    window.history.pushState({}, '', '/auth/reset-password?token=bad-token')

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

      if (url.endsWith('/auth/password-reset/confirm')) {
        return Promise.resolve({
          ok: false,
          status: 400,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: false,
              error: {
                code: 'HTTP_ERROR',
                message: 'Invalid or expired reset token',
              },
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/auth/reset-password')

    render(
      <AppProviders>
        <mod.ResetPasswordPage />
      </AppProviders>,
    )

    expect(screen.getByLabelText('重置令牌')).toHaveValue('bad-token')

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('新密码'), 'new-password-123')
    await user.click(screen.getByRole('button', { name: '重置密码' }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        '重置链接无效或已过期',
      )
    })
  })

  it('given_token_when_confirm_success_then_shows_success_and_login_hint', async () => {
    window.history.pushState({}, '', '/auth/reset-password?token=good-token')

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

      if (url.endsWith('/auth/password-reset/confirm')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              success: true,
              message: 'Password reset successful',
            }),
        })
      }

      throw new Error(`unexpected fetch url: ${url}`)
    })
    vi.stubGlobal('fetch', mockFetch)

    const mod = await import('../../../app/routes/auth/reset-password')

    render(
      <AppProviders>
        <mod.ResetPasswordPage />
      </AppProviders>,
    )

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('新密码'), 'new-password-123')
    await user.click(screen.getByRole('button', { name: '重置密码' }))

    await waitFor(() => {
      expect(
        screen.getByText('密码已重置，请使用新密码重新登录。'),
      ).toBeInTheDocument()
    })
  })
})

