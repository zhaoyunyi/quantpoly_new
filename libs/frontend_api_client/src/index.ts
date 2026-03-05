/**
 * Frontend API Client — 公开导出
 */

// 错误模型
export {
  type AppError,
  type AppErrorKind,
  httpStatusToKind,
  createAppError,
  networkError,
  timeoutError,
  isAuthError,
} from './errors'

// 信封解包
export {
  type SuccessEnvelope,
  type ErrorEnvelope,
  type PagedData,
  type Envelope,
  unwrapEnvelope,
  unwrapPagedEnvelope,
  isSuccessEnvelope,
  parseEnvelope,
} from './envelope'

// 请求核心
export {
  type ClientConfig,
  type RequestOptions,
  configureClient,
  getClientConfig,
  request,
  get,
  post,
  patch,
  put,
  del,
} from './request'

// Endpoints
export {
  type UserProfile,
  type LoginPayload,
  type RegisterPayload,
  type LoginResult,
  type HealthResult,
  type UserPreferences,
  type ChangePasswordResult,
  type DeleteAccountResult,
  healthCheck,
  login,
  register,
  logout,
  getMe,
  updateMe,
  changePassword,
  deleteAccount,
  getPreferences,
  patchPreferences,
} from './endpoints'

// React hooks
export { AuthProvider, useAuth, type AuthState } from './hooks'
