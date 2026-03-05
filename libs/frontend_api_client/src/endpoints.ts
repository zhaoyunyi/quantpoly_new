/**
 * Frontend API Client — 最小 endpoints 封装
 *
 * Auth / Me / Preferences / Health 样例接口。
 * 页面/组件仅通过这些函数访问后端，禁止直接 fetch。
 */

import { get, post, patch, del } from './request'

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

export interface HealthResult {
  status: string
  enabledContexts: string[]
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
