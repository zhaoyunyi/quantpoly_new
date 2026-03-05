/**
 * Frontend API Client — errors.test.ts
 *
 * GIVEN: AppError 模型
 * WHEN:  映射 HTTP 状态码 / 创建错误实例
 * THEN:  返回正确的 kind / code / message
 */

import { describe, it, expect } from 'vitest'
import {
  httpStatusToKind,
  createAppError,
  networkError,
  timeoutError,
  isAuthError,
} from '@qp/api-client/errors'

describe('errors', () => {
  describe('http_status_to_kind', () => {
    it('given_401_when_mapped_then_returns_auth', () => {
      expect(httpStatusToKind(401)).toBe('auth')
    })

    it('given_403_when_mapped_then_returns_auth', () => {
      expect(httpStatusToKind(403)).toBe('auth')
    })

    it('given_404_when_mapped_then_returns_not_found', () => {
      expect(httpStatusToKind(404)).toBe('not_found')
    })

    it('given_410_when_mapped_then_returns_not_found', () => {
      expect(httpStatusToKind(410)).toBe('not_found')
    })

    it('given_409_when_mapped_then_returns_conflict', () => {
      expect(httpStatusToKind(409)).toBe('conflict')
    })

    it('given_422_when_mapped_then_returns_validation', () => {
      expect(httpStatusToKind(422)).toBe('validation')
    })

    it('given_500_when_mapped_then_returns_server', () => {
      expect(httpStatusToKind(500)).toBe('server')
    })

    it('given_503_when_mapped_then_returns_server', () => {
      expect(httpStatusToKind(503)).toBe('server')
    })

    it('given_400_when_mapped_then_returns_unknown', () => {
      expect(httpStatusToKind(400)).toBe('unknown')
    })
  })

  describe('create_app_error', () => {
    it('given_params_when_created_then_has_all_fields', () => {
      const err = createAppError('auth', 'UNAUTHORIZED', '未认证', 401, 'req-1')
      expect(err).toEqual({
        kind: 'auth',
        code: 'UNAUTHORIZED',
        message: '未认证',
        httpStatus: 401,
        requestId: 'req-1',
      })
    })
  })

  describe('network_error', () => {
    it('given_message_when_created_then_kind_is_network', () => {
      const err = networkError('连接被拒绝')
      expect(err.kind).toBe('network')
      expect(err.code).toBe('NETWORK_ERROR')
      expect(err.message).toBe('连接被拒绝')
    })
  })

  describe('timeout_error', () => {
    it('given_timeout_when_created_then_has_timeout_code', () => {
      const err = timeoutError()
      expect(err.kind).toBe('network')
      expect(err.code).toBe('TIMEOUT')
    })
  })

  describe('is_auth_error', () => {
    it('given_auth_error_when_checked_then_returns_true', () => {
      const err = createAppError('auth', 'UNAUTHORIZED', '未认证')
      expect(isAuthError(err)).toBe(true)
    })

    it('given_network_error_when_checked_then_returns_false', () => {
      const err = networkError('fail')
      expect(isAuthError(err)).toBe(false)
    })
  })
})
