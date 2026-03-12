/**
 * Frontend API Client — 最小 endpoints 封装
 *
 * Auth / Me / Preferences / Health 样例接口。
 * 页面/组件仅通过这些函数访问后端，禁止直接 fetch。
 */

import { get, post, put, patch, del } from './request'

/* ─── 类型定义 ─── */

export interface UserProfile {
  id: string
  email: string
  displayName: string | null
  emailVerified: boolean
  isActive: boolean
  role: 'user' | 'admin'
  level: number
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
}

export interface LoginResult {
  token: string
}

export interface VerifyEmailPayload {
  email: string
}

export interface PasswordResetRequestPayload {
  email: string
}

export interface PasswordResetRequestResult {
  resetToken: string
}

export interface PasswordResetConfirmPayload {
  token: string
  newPassword: string
}

export interface HealthResult {
  status: string
  enabledContexts: string[]
}

/* ─── Monitoring / Summary ─── */

export interface MonitorSummary {
  type: 'monitor.summary'
  generatedAt: string
  metadata: {
    version: string
    latencyMs: number
    sources: Record<string, 'ok' | 'degraded'>
  }
  accounts: { total: number; active: number }
  strategies: { total: number; active: number }
  backtests: {
    total: number
    pending: number
    running: number
    completed: number
    failed: number
    cancelled: number
  }
  tasks: {
    total: number
    queued: number
    running: number
    succeeded: number
    failed: number
    cancelled: number
  }
  signals: { total: number; pending: number; expired: number }
  alerts: { total: number; open: number; critical: number }
  degraded: { enabled: boolean; reasons: string[] }
  isEmpty: boolean
}

export function getMonitorSummary(): Promise<MonitorSummary> {
  return get<MonitorSummary>('/monitor/summary')
}

/* ─── Trading / Analytics ─── */

export interface TradingAccountsAggregate {
  userId: string
  accountCount: number
  totalCashBalance: number
  totalMarketValue: number
  totalUnrealizedPnl: number
  totalEquity: number
  totalTradeCount: number
  totalTurnover: number
  pendingOrderCount: number
}

export function getTradingAccountsAggregate(): Promise<TradingAccountsAggregate> {
  return get<TradingAccountsAggregate>('/trading/accounts/aggregate')
}

/* ─── Backtests ─── */

export interface BacktestStatistics {
  pendingCount: number
  runningCount: number
  completedCount: number
  failedCount: number
  cancelledCount: number
  totalCount: number
  averageReturnRate: number
  averageMaxDrawdown: number
  averageWinRate: number
}

export function getBacktestStatistics(): Promise<BacktestStatistics> {
  return get<BacktestStatistics>('/backtests/statistics')
}

/* ─── Risk / Alerts ─── */

export interface RiskAlertStats {
  total: number
  open: number
  acknowledged: number
  resolved: number
  bySeverity: Record<string, number>
}

export interface RiskAlert {
  id: string
  userId: string
  accountId: string
  ruleName: string
  severity: string
  message: string
  status: string
  createdAt: string | null
  acknowledgedAt: string | null
  acknowledgedBy: string | null
  resolvedAt: string | null
  resolvedBy: string | null
  notificationStatus: string | null
  notifiedAt: string | null
  notifiedBy: string | null
}

function _withQuery(
  path: string,
  query: Record<string, string | number | boolean | undefined | null>,
): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    const normalized = String(value).trim()
    if (!normalized) continue
    params.set(key, normalized)
  }
  const qs = params.toString()
  return qs ? `${path}?${qs}` : path
}

export function getRiskAlertStats(params?: { accountId?: string }): Promise<RiskAlertStats> {
  const path = _withQuery('/risk/alerts/stats', {
    accountId: params?.accountId,
  })
  return get<RiskAlertStats>(path)
}

export function getRiskAlerts(params?: {
  accountId?: string
  unresolvedOnly?: boolean
}): Promise<RiskAlert[]> {
  const path = _withQuery('/risk/alerts', {
    accountId: params?.accountId,
    unresolvedOnly: params?.unresolvedOnly ? 'true' : undefined,
  })
  return get<RiskAlert[]>(path)
}

export function acknowledgeRiskAlert(alertId: string): Promise<RiskAlert> {
  const id = encodeURIComponent(alertId)
  return patch<RiskAlert>(`/risk/alerts/${id}/acknowledge`)
}

export function resolveRiskAlert(alertId: string): Promise<{ resolved: boolean }> {
  const id = encodeURIComponent(alertId)
  return post<{ resolved: boolean }>(`/risk/alerts/${id}/resolve`)
}

/* ─── Signals ─── */

export interface SignalsDashboard {
  total: number
  pending: number
  expired: number
  executed: number
  cancelled: number
  byAccount: Array<{
    accountId: string
    total: number
    pending: number
    expired: number
    executed: number
    cancelled: number
  }>
}

export function getSignalsDashboard(params?: { accountId?: string }): Promise<SignalsDashboard> {
  const path = _withQuery('/signals/dashboard', {
    accountId: params?.accountId,
  })
  return get<SignalsDashboard>(path)
}

export interface TradingSignal {
  id: string
  userId: string
  strategyId: string
  accountId: string
  symbol: string
  side: string
  status: string
  createdAt: string | null
  updatedAt: string | null
  expiresAt: string | null
  metadata: Record<string, unknown>
  risk?: unknown
}

export function getSignals(params?: {
  keyword?: string
  strategyId?: string
  accountId?: string
  symbol?: string
  status?: string
}): Promise<TradingSignal[]> {
  const path = _withQuery('/signals', {
    keyword: params?.keyword,
    strategyId: params?.strategyId,
    accountId: params?.accountId,
    symbol: params?.symbol,
    status: params?.status,
  })
  return get<TradingSignal[]>(path)
}

export function searchSignals(params?: {
  keyword?: string
  strategyId?: string
  accountId?: string
  symbol?: string
  status?: string
}): Promise<TradingSignal[]> {
  const path = _withQuery('/signals/search', {
    keyword: params?.keyword,
    strategyId: params?.strategyId,
    accountId: params?.accountId,
    symbol: params?.symbol,
    status: params?.status,
  })
  return get<TradingSignal[]>(path)
}

export function getSignalsPending(): Promise<TradingSignal[]> {
  return get<TradingSignal[]>('/signals/pending')
}

export function processSignal(signalId: string): Promise<TradingSignal> {
  const id = encodeURIComponent(signalId)
  return post<TradingSignal>(`/signals/${id}/process`)
}

export function executeSignal(signalId: string): Promise<TradingSignal> {
  const id = encodeURIComponent(signalId)
  return post<TradingSignal>(`/signals/${id}/execute`)
}

export function cancelSignal(signalId: string): Promise<TradingSignal> {
  const id = encodeURIComponent(signalId)
  return post<TradingSignal>(`/signals/${id}/cancel`)
}

/* ─── Strategy Management ─── */

export type StrategyStatus = 'draft' | 'active' | 'inactive' | 'archived'

export interface StrategyTemplate {
  templateId: string
  name: string
  requiredParameters: Record<string, {
    type: string
    min?: number
    max?: number
  }>
  defaults: Record<string, unknown>
}

export interface StrategyItem {
  id: string
  userId: string
  name: string
  template: string
  parameters: Record<string, unknown>
  status: StrategyStatus
  createdAt: string
  updatedAt: string
}

export interface StrategyListResult {
  items: StrategyItem[]
  total: number
  page: number
  pageSize: number
}

export interface CreateStrategyPayload {
  name: string
  template: string
  parameters: Record<string, unknown>
}

export interface CreateStrategyFromTemplatePayload {
  name: string
  templateId: string
  parameters: Record<string, unknown>
}

export interface UpdateStrategyPayload {
  name?: string
  parameters?: Record<string, unknown>
}

export interface ValidateExecutionPayload {
  parameters: Record<string, unknown>
}

export interface ValidateExecutionResult {
  valid: boolean
  strategyId: string
  template: string
}

export interface StrategyBacktest {
  id: string
  userId: string
  strategyId: string
  status: string
  config: Record<string, unknown>
  metrics: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface StrategyBacktestListResult {
  items: StrategyBacktest[]
  total: number
  page: number
  pageSize: number
}

export interface StrategyBacktestStats {
  pendingCount: number
  runningCount: number
  completedCount: number
  failedCount: number
  cancelledCount: number
  totalCount: number
  averageReturnRate: number
  averageMaxDrawdown: number
  averageWinRate: number
}

export interface CreateBacktestForStrategyPayload {
  config: Record<string, unknown>
  idempotencyKey?: string
}

export interface ResearchPerformanceTaskPayload {
  analysisPeriodDays?: number
  idempotencyKey?: string
}

export interface ResearchOptimizationTaskPayload {
  method?: string
  objective?: Record<string, unknown>
  parameterSpace?: Record<string, Record<string, unknown>>
  constraints?: Record<string, unknown>
  budget?: Record<string, unknown>
  idempotencyKey?: string
}

export interface ResearchTaskResult {
  taskId: string
  taskType: string
  status: string
  result: Record<string, unknown> | null
}

export interface ResearchResultsListing {
  items: Array<Record<string, unknown>>
  total: number
}

export function getStrategyTemplates(): Promise<StrategyTemplate[]> {
  return get<StrategyTemplate[]>('/strategies/templates')
}

export function getStrategies(params?: {
  status?: string
  search?: string
  page?: number
  pageSize?: number
}): Promise<StrategyListResult> {
  const path = _withQuery('/strategies', {
    status: params?.status,
    search: params?.search,
    page: params?.page,
    pageSize: params?.pageSize,
  })
  return get<StrategyListResult>(path)
}

export function getStrategy(strategyId: string): Promise<StrategyItem> {
  const id = encodeURIComponent(strategyId)
  return get<StrategyItem>(`/strategies/${id}`)
}

export function createStrategy(payload: CreateStrategyPayload): Promise<StrategyItem> {
  return post<StrategyItem>('/strategies', payload)
}

export function createStrategyFromTemplate(
  payload: CreateStrategyFromTemplatePayload,
): Promise<StrategyItem> {
  return post<StrategyItem>('/strategies/from-template', payload)
}

export function updateStrategy(
  strategyId: string,
  payload: UpdateStrategyPayload,
): Promise<StrategyItem> {
  const id = encodeURIComponent(strategyId)
  return put<StrategyItem>(`/strategies/${id}`, payload)
}

export function deleteStrategy(strategyId: string): Promise<{ deleted: boolean }> {
  const id = encodeURIComponent(strategyId)
  return del<{ deleted: boolean }>(`/strategies/${id}`)
}

export function activateStrategy(strategyId: string): Promise<StrategyItem> {
  const id = encodeURIComponent(strategyId)
  return post<StrategyItem>(`/strategies/${id}/activate`)
}

export function deactivateStrategy(strategyId: string): Promise<StrategyItem> {
  const id = encodeURIComponent(strategyId)
  return post<StrategyItem>(`/strategies/${id}/deactivate`)
}

export function archiveStrategy(strategyId: string): Promise<StrategyItem> {
  const id = encodeURIComponent(strategyId)
  return post<StrategyItem>(`/strategies/${id}/archive`)
}

export function validateExecution(
  strategyId: string,
  payload: ValidateExecutionPayload,
): Promise<ValidateExecutionResult> {
  const id = encodeURIComponent(strategyId)
  return post<ValidateExecutionResult>(`/strategies/${id}/validate-execution`, payload)
}

export function getStrategyBacktests(
  strategyId: string,
  params?: { status?: string; page?: number; pageSize?: number },
): Promise<StrategyBacktestListResult> {
  const id = encodeURIComponent(strategyId)
  const path = _withQuery(`/strategies/${id}/backtests`, {
    status: params?.status,
    page: params?.page,
    pageSize: params?.pageSize,
  })
  return get<StrategyBacktestListResult>(path)
}

export function getStrategyBacktestStats(
  strategyId: string,
): Promise<StrategyBacktestStats> {
  const id = encodeURIComponent(strategyId)
  return get<StrategyBacktestStats>(`/strategies/${id}/backtest-stats`)
}

export function createBacktestForStrategy(
  strategyId: string,
  payload: CreateBacktestForStrategyPayload,
): Promise<StrategyBacktest> {
  const id = encodeURIComponent(strategyId)
  return post<StrategyBacktest>(`/strategies/${id}/backtests`, payload)
}

export function submitResearchPerformanceTask(
  strategyId: string,
  payload: ResearchPerformanceTaskPayload,
): Promise<ResearchTaskResult> {
  const id = encodeURIComponent(strategyId)
  return post<ResearchTaskResult>(`/strategies/${id}/research/performance-task`, payload)
}

export function submitResearchOptimizationTask(
  strategyId: string,
  payload?: ResearchOptimizationTaskPayload,
): Promise<ResearchTaskResult> {
  const id = encodeURIComponent(strategyId)
  return post<ResearchTaskResult>(`/strategies/${id}/research/optimization-task`, payload)
}

export function getResearchResults(
  strategyId: string,
  params?: { status?: string; method?: string; version?: string; limit?: number },
): Promise<ResearchResultsListing> {
  const id = encodeURIComponent(strategyId)
  const path = _withQuery(`/strategies/${id}/research/results`, {
    status: params?.status,
    method: params?.method,
    version: params?.version,
    limit: params?.limit,
  })
  return get<ResearchResultsListing>(path)
}

/* ─── Backtests Compare ─── */

export interface BacktestCompareResult {
  taskIds: string[]
  metrics: Array<Record<string, unknown>>
}

export function compareBacktests(
  taskIds: string[],
): Promise<BacktestCompareResult> {
  return post<BacktestCompareResult>('/backtests/compare', { taskIds })
}

export type UserPreferences = Record<string, unknown>

export interface ChangePasswordResult {
  revokedSessions: number
}

export interface DeleteAccountResult {
  revokedSessions: number
}

/* ─── Health ─── */

export function healthCheck(): Promise<HealthResult> {
  return get<HealthResult>('/health')
}

/* ─── Auth ─── */

export function login(payload: LoginPayload): Promise<LoginResult> {
  return post<LoginResult>('/auth/login', payload)
}

export function register(payload: RegisterPayload): Promise<void> {
  return post<void>('/auth/register', payload)
}

export function logout(): Promise<void> {
  return post<void>('/auth/logout')
}

export function verifyEmail(payload: VerifyEmailPayload): Promise<void> {
  return post<void>('/auth/verify-email', payload)
}

export function resendVerification(payload: VerifyEmailPayload): Promise<void> {
  return post<void>('/auth/verify-email/resend', payload)
}

/**
 * 发起密码重置请求。
 *
 * 后端在测试模式下可能返回 resetToken（便于端到端测试），
 * 非测试模式则不返回 data。
 */
export function requestPasswordReset(
  payload: PasswordResetRequestPayload,
): Promise<PasswordResetRequestResult | undefined> {
  return post<PasswordResetRequestResult | undefined>(
    '/auth/password-reset/request',
    payload,
  )
}

export function confirmPasswordReset(
  payload: PasswordResetConfirmPayload,
): Promise<void> {
  return post<void>('/auth/password-reset/confirm', payload)
}

/* ─── Users / Me ─── */

export function getMe(): Promise<UserProfile> {
  return get<UserProfile>('/users/me')
}

export function updateMe(
  updates: Partial<Pick<UserProfile, 'email' | 'displayName'>>,
): Promise<UserProfile> {
  return patch<UserProfile>('/users/me', updates)
}

export function changePassword(payload: {
  currentPassword: string
  newPassword: string
  revokeAllSessions?: boolean
}): Promise<ChangePasswordResult> {
  return patch<ChangePasswordResult>('/users/me/password', payload)
}

export function deleteAccount(): Promise<DeleteAccountResult> {
  return del<DeleteAccountResult>('/users/me')
}

/* ─── Preferences ─── */

export function getPreferences(): Promise<UserPreferences> {
  return get<UserPreferences>('/users/me/preferences')
}

export function patchPreferences(
  patchBody: Record<string, unknown>,
): Promise<UserPreferences> {
  return patch<UserPreferences>('/users/me/preferences', patchBody)
}
