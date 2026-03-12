/**
 * Frontend API Client — 后端 envelope 解包
 *
 * 适配后端统一响应格式：
 * - 成功：{ success: true, message: "...", data?: ... }
 * - 错误：{ success: false, error: { code: "...", message: "..." } }
 * - 分页：{ success: true, data: { items: [...], total, page, pageSize } }
 */

import {
  type AppError,
  createAppError,
  httpStatusToKind,
} from './errors'

/* ─── 后端信封类型 ─── */

export type SuccessEnvelope<T = unknown> =
  T extends void | undefined
    ? {
        success: true
        message: string
        data?: T
      }
    : {
        success: true
        message: string
        data: T
      }

export interface ErrorEnvelope {
  success: false
  error: {
    code: string
    message: string
  }
}

export interface PagedData<T = unknown> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export type Envelope<T = unknown> = SuccessEnvelope<T> | ErrorEnvelope

/* ─── 解包函数 ─── */

/**
 * 解包后端 success_response。
 * 如果信封指示失败，则抛出 AppError 结构。
 */
export function unwrapEnvelope<T>(
  envelope: Envelope<T>,
  httpStatus: number,
): T {
  if (envelope.success) {
    // 对于 T=void/undefined 的接口，后端可能省略 data 字段。
    // 在 strictNullChecks 下 envelope.data 会被推断为 T | undefined，因此需要显式处理。
    if (envelope.data === undefined) {
      return undefined as T
    }
    return envelope.data
  }
  throw createAppError(
    httpStatusToKind(httpStatus),
    envelope.error.code,
    envelope.error.message,
    httpStatus,
  )
}

/**
 * 解包后端 paged_response。
 */
export function unwrapPagedEnvelope<T>(
  envelope: Envelope<PagedData<T>>,
  httpStatus: number,
): PagedData<T> {
  return unwrapEnvelope(envelope, httpStatus)
}

/**
 * 类型守卫：判断响应是否为成功信封
 */
export function isSuccessEnvelope<T>(
  envelope: Envelope<T>,
): envelope is SuccessEnvelope<T> {
  return envelope.success === true
}

/**
 * 从任意 JSON 解析信封，带基本类型校验
 */
export function parseEnvelope(json: unknown): Envelope {
  if (
    typeof json === 'object' &&
    json !== null &&
    'success' in json
  ) {
    return json as Envelope
  }
  throw createAppError(
    'unknown',
    'INVALID_ENVELOPE',
    '后端响应格式异常',
  )
}
