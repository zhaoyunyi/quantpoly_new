/**
 * Frontend API Client — request.test.ts
 *
 * GIVEN: fetch 封装
 * WHEN:  成功请求 / 超时 / 网络错误 / 401
 * THEN:  正确解包或抛出 AppError
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { request, configureClient } from '@qp/api-client/request'
import type { AppError } from '@qp/api-client/errors'

describe('request', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    configureClient({ baseUrl: 'http://localhost:8000', timeout: 5000 })
    mockFetch.mockReset()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('given_success_response_when_get_then_returns_data', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          success: true,
          message: 'ok',
          data: { userId: 'u1' },
        }),
    })

    const result = await request('/users/me')
    expect(result).toEqual({ userId: 'u1' })
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/users/me',
      expect.objectContaining({
        method: 'GET',
        credentials: 'include',
      }),
    )
  })

  it('given_401_response_when_get_then_throws_auth_error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          success: false,
          error: { code: 'UNAUTHORIZED', message: '未认证' },
        }),
    })

    try {
      await request('/users/me')
      expect.unreachable()
    } catch (err) {
      const appErr = err as AppError
      expect(appErr.kind).toBe('auth')
      expect(appErr.code).toBe('UNAUTHORIZED')
      expect(appErr.httpStatus).toBe(401)
    }
  })

  it('given_network_failure_when_get_then_throws_network_error', async () => {
    mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))

    try {
      await request('/health')
      expect.unreachable()
    } catch (err) {
      const appErr = err as AppError
      expect(appErr.kind).toBe('network')
      expect(appErr.code).toBe('NETWORK_ERROR')
    }
  })

  it('given_abort_when_timeout_then_throws_timeout_error', async () => {
    mockFetch.mockRejectedValue(
      new DOMException('The operation was aborted.', 'AbortError'),
    )

    try {
      await request('/health', { timeout: 1 })
      expect.unreachable()
    } catch (err) {
      const appErr = err as AppError
      expect(appErr.kind).toBe('network')
      expect(appErr.code).toBe('TIMEOUT')
    }
  })

  it('given_post_body_when_post_then_sends_json', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          success: true,
          message: 'ok',
          data: { token: 'abc' },
        }),
    })

    const result = await request('/auth/login', {
      method: 'POST',
      body: { email: 'a@b.com', password: '123' },
    })

    expect(result).toEqual({ token: 'abc' })
    // 验证 fetch 被正确调用
    expect(mockFetch).toHaveBeenCalledOnce()
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('http://localhost:8000/auth/login')
    expect(opts.method).toBe('POST')
    expect(opts.credentials).toBe('include')
  })

  it('given_non_json_response_when_200_then_returns_undefined', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 204,
      headers: new Headers({ 'content-type': '' }),
    })

    const result = await request('/auth/logout')
    expect(result).toBeUndefined()
  })
})
