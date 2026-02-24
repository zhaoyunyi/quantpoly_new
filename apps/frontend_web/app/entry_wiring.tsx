/// <reference types="vite/client" />
/**
 * Frontend Entry Wiring
 *
 * 入口级“接线层”：
 * - 统一配置 API client baseUrl（直连后端）
 * - 全局 Providers（Auth/Toast/ErrorBoundary）
 * - 受保护页面外壳（AuthGuard + AppShell）
 */

import type { ReactNode } from 'react'

import { configureClient } from '@qp/api-client'
import { AuthProvider } from '@qp/api-client'
import type { UserProfile } from '@qp/api-client'
import { ToastProvider } from '@qp/ui'
import { AppShell, AuthGuard, ErrorBoundary } from '@qp/shell'

const FALLBACK_BACKEND_ORIGIN = 'http://localhost:8000'

/** 标准化后端 origin（去空格、去尾部 /、提供默认值） */
export function normalizeBackendOrigin(origin: string | undefined): string {
  const raw = (origin ?? '').trim()
  const base = raw || FALLBACK_BACKEND_ORIGIN
  return base.replace(/\/+$/, '')
}

/**
 * 初始化前端 API Client（应用启动时调用）。
 * 备注：该函数是幂等的，重复调用会覆盖同名配置。
 */
export function bootstrapApiClient(origin?: string): void {
  const resolved = normalizeBackendOrigin(
    origin ?? import.meta.env.VITE_BACKEND_ORIGIN,
  )
  configureClient({ baseUrl: resolved })
}

/** 全局 Providers：错误边界 + 认证 + Toast */
export interface InitialAuthState {
  user: UserProfile | null
  resolved: boolean
}

export function AppProviders({
  children,
  initialAuth,
}: {
  children: ReactNode
  initialAuth?: InitialAuthState
}) {
  return (
    <ErrorBoundary>
      <AuthProvider
        initialUser={initialAuth?.user ?? null}
        initialResolved={initialAuth?.resolved ?? false}
      >
        <ToastProvider>{children}</ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

/**
 * 受保护页面外壳（标准模式）。
 * 页面只需要在内部编排业务 UI；鉴权与导航由该外壳统一处理。
 */
export function ProtectedLayout({ children }: { children: ReactNode }) {
  const currentPath =
    typeof window !== 'undefined' ? window.location.pathname : '/'
  return (
    <AuthGuard>
      <AppShell currentPath={currentPath}>{children}</AppShell>
    </AuthGuard>
  )
}
