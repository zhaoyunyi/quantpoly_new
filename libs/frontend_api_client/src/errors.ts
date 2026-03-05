/**
 * Frontend API Client — 统一错误模型
 *
 * 将后端 error_response 与网络异常映射为稳定 AppError，
 * 供 UI 统一展示与处理。
 */

/** 错误分类 */
export type AppErrorKind =
  | 'auth' // 认证/会话相关
  | 'validation' // 参数校验
  | 'not_found' // 资源不存在
  | 'conflict' // 资源冲突
  | 'server' // 服务端错误（5xx）
  | 'network' // 网络不可达 / 超时
  | 'unknown' // 未知错误

export interface AppError {
  kind: AppErrorKind
  code: string
  message: string
  httpStatus?: number
  requestId?: string
}

/** 从 HTTP 状态码推断错误分类 */
export function httpStatusToKind(status: number): AppErrorKind {
  if (status === 401 || status === 403) return 'auth'
  if (status === 404 || status === 410) return 'not_found'
  if (status === 409) return 'conflict'
  if (status === 422) return 'validation'
  if (status >= 500) return 'server'
  return 'unknown'
}

/** 创建 AppError 快捷函数 */
export function createAppError(
  kind: AppErrorKind,
  code: string,
  message: string,
  httpStatus?: number,
  requestId?: string,
): AppError {
  return { kind, code, message, httpStatus, requestId }
}

/** 网络错误工厂 */
export function networkError(message: string): AppError {
  return createAppError('network', 'NETWORK_ERROR', message)
}

/** 超时错误工厂 */
export function timeoutError(): AppError {
  return createAppError('network', 'TIMEOUT', '请求超时，请稍后再试')
}

/** 判断是否为认证类错误 */
export function isAuthError(error: AppError): boolean {
  return error.kind === 'auth'
}
