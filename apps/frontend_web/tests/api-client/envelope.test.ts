/**
 * Frontend API Client — envelope.test.ts
 *
 * GIVEN: 后端 envelope 格式
 * WHEN:  解包 success / error / 分页 / 非法响应
 * THEN:  正确提取 data 或抛出 AppError
 */

import { describe, it, expect } from 'vitest'
import {
  unwrapEnvelope,
  unwrapPagedEnvelope,
  isSuccessEnvelope,
  parseEnvelope,
} from '@qp/api-client/envelope'
import type { AppError } from '@qp/api-client/errors'

describe('envelope', () => {
  describe('unwrap_envelope', () => {
    it('given_success_envelope_when_unwrapped_then_returns_data', () => {
      const envelope = {
        success: true as const,
        message: 'ok',
        data: { userId: '123' },
      }
      const result = unwrapEnvelope(envelope, 200)
      expect(result).toEqual({ userId: '123' })
    })

    it('given_error_envelope_when_unwrapped_then_throws_app_error', () => {
      const envelope = {
        success: false as const,
        error: { code: 'USER_NOT_FOUND', message: '用户不存在' },
      }
      try {
        unwrapEnvelope(envelope, 404)
        expect.unreachable()
      } catch (err) {
        const appErr = err as AppError
        expect(appErr.kind).toBe('not_found')
        expect(appErr.code).toBe('USER_NOT_FOUND')
        expect(appErr.message).toBe('用户不存在')
        expect(appErr.httpStatus).toBe(404)
      }
    })

    it('given_401_error_when_unwrapped_then_kind_is_auth', () => {
      const envelope = {
        success: false as const,
        error: { code: 'UNAUTHORIZED', message: '未认证' },
      }
      try {
        unwrapEnvelope(envelope, 401)
        expect.unreachable()
      } catch (err) {
        const appErr = err as AppError
        expect(appErr.kind).toBe('auth')
      }
    })
  })

  describe('unwrap_paged_envelope', () => {
    it('given_paged_success_when_unwrapped_then_returns_paged_data', () => {
      const envelope = {
        success: true as const,
        message: 'ok',
        data: {
          items: [{ id: 1 }, { id: 2 }],
          total: 50,
          page: 1,
          pageSize: 10,
        },
      }
      const result = unwrapPagedEnvelope(envelope, 200)
      expect(result.items).toHaveLength(2)
      expect(result.total).toBe(50)
      expect(result.page).toBe(1)
      expect(result.pageSize).toBe(10)
    })
  })

  describe('is_success_envelope', () => {
    it('given_success_envelope_when_checked_then_returns_true', () => {
      const envelope = { success: true as const, message: 'ok', data: null }
      expect(isSuccessEnvelope(envelope)).toBe(true)
    })

    it('given_error_envelope_when_checked_then_returns_false', () => {
      const envelope = {
        success: false as const,
        error: { code: 'X', message: 'x' },
      }
      expect(isSuccessEnvelope(envelope)).toBe(false)
    })
  })

  describe('parse_envelope', () => {
    it('given_valid_json_when_parsed_then_returns_envelope', () => {
      const json = { success: true, message: 'ok', data: {} }
      const result = parseEnvelope(json)
      expect(result.success).toBe(true)
    })

    it('given_invalid_json_when_parsed_then_throws', () => {
      expect(() => parseEnvelope('not_json')).toThrow()
      expect(() => parseEnvelope(null)).toThrow()
      expect(() => parseEnvelope({ foo: 'bar' })).toThrow()
    })
  })
})
