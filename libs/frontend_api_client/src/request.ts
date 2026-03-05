/**
 * Frontend API Client — 统一 fetch 封装
 *
 * - baseUrl + credentials: include（cookie session）
 * - 超时控制
 * - JSON/文本响应自动判断
 * - 网络异常 → AppError 映射
 */

import {
  type AppError,
  createAppError,
  httpStatusToKind,
  networkError,
  timeoutError,
} from './errors'
import { type Envelope, parseEnvelope, unwrapEnvelope } from './envelope'

/* ─── 配置 ─── */

export interface ClientConfig {
  /** 后端 API 基础 URL，例如 http://localhost:8000 */
  baseUrl: string
  /** 请求超时时间（毫秒），默认 10000 */
  timeout?: number
}

let _config: ClientConfig = {
  baseUrl: '',
  timeout: 10_000,
}

/** 初始化 API Client 配置（应用启动时调用一次） */
export function configureClient(config: ClientConfig): void {
  _config = { ..._config, ...config }
}

/** 获取当前配置 */
export function getClientConfig(): Readonly<ClientConfig> {
  return _config
}

/* ─── 请求选项 ─── */

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
  /** 单次请求覆盖超时（毫秒） */
  timeout?: number
  /** 是否跳过 envelope 解包（直接返回原始响应） */
  raw?: boolean
}

/* ─── 核心 request ─── */

/**
 * 发起后端请求，自动携带 cookie、处理超时、解包 envelope。
 *
 * @returns 解包后的 data 字段
 * @throws AppError
 */
export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = 'GET',
    body,
    headers: extraHeaders,
    timeout = _config.timeout ?? 10_000,
  } = options

  const url = `${_config.baseUrl}${path}`

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...extraHeaders,
  }

  let fetchBody: string | undefined
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    fetchBody = JSON.stringify(body)
  }

  // 超时控制
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: fetchBody,
      credentials: 'include',
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw timeoutError()
    }
    throw networkError(
      err instanceof Error ? err.message : '网络请求失败',
    )
  } finally {
    clearTimeout(timer)
  }

  // 解析响应体
  const contentType = response.headers.get('content-type') ?? ''

  if (options.raw) {
    return response as unknown as T
  }

  if (!contentType.includes('application/json')) {
    // 非 JSON 响应（如 204 No Content）
    if (response.ok) {
      return undefined as T
    }
    throw createAppError(
      httpStatusToKind(response.status),
      'NON_JSON_ERROR',
      `服务端返回了非 JSON 响应 (${response.status})`,
      response.status,
    )
  }

  let json: unknown
  try {
    json = await response.json()
  } catch {
    throw createAppError(
      'unknown',
      'JSON_PARSE_ERROR',
      '响应 JSON 解析失败',
      response.status,
    )
  }

  const envelope = parseEnvelope(json)
  return unwrapEnvelope<T>(envelope as Envelope<T>, response.status)
}

/* ─── 语法糖 ─── */

export function get<T = unknown>(
  path: string,
  options?: Omit<RequestOptions, 'method' | 'body'>,
): Promise<T> {
  return request<T>(path, { ...options, method: 'GET' })
}

export function post<T = unknown>(
  path: string,
  body?: unknown,
  options?: Omit<RequestOptions, 'method' | 'body'>,
): Promise<T> {
  return request<T>(path, { ...options, method: 'POST', body })
}

export function patch<T = unknown>(
  path: string,
  body?: unknown,
  options?: Omit<RequestOptions, 'method' | 'body'>,
): Promise<T> {
  return request<T>(path, { ...options, method: 'PATCH', body })
}

export function put<T = unknown>(
  path: string,
  body?: unknown,
  options?: Omit<RequestOptions, 'method' | 'body'>,
): Promise<T> {
  return request<T>(path, { ...options, method: 'PUT', body })
}

export function del<T = unknown>(
  path: string,
  options?: Omit<RequestOptions, 'method' | 'body'>,
): Promise<T> {
  return request<T>(path, { ...options, method: 'DELETE' })
}
