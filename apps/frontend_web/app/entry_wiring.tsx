/// <reference types="vite/client" />
/**
 * Frontend Entry Wiring
 *
 * 入口级“接线层”：
 * - 统一配置 API client baseUrl（直连后端）
 * - 全局 Providers（Auth/Toast/ErrorBoundary）
 * - 受保护页面外壳（AuthGuard + AppShell）
 */

import { type ReactNode, useCallback, useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'

import { configureClient } from '@qp/api-client'
import { AuthProvider } from '@qp/api-client'
import type { UserProfile } from '@qp/api-client'
import { useAuth } from '@qp/api-client'
import { ToastProvider } from '@qp/ui'
import { ThemeProvider } from '@qp/ui'
import { AppShell, AuthGuard, ErrorBoundary } from '@qp/shell'
import { NotificationBell } from './widgets/notifications/NotificationBell'
import { NotificationPanel } from './widgets/notifications/NotificationPanel'
import { useNotifications } from './shared/useNotifications'
import { useHotkey } from './shared/useHotkey'
import { CommandPalette } from './widgets/search/CommandPalette'

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
      <ThemeProvider>
        <AuthProvider
          initialUser={initialAuth?.user ?? null}
          initialResolved={initialAuth?.resolved ?? false}
        >
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

/**
 * 受保护页面外壳（标准模式）。
 * 页面只需要在内部编排业务 UI；鉴权与导航由该外壳统一处理。
 */
export function ProtectedLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const currentPath =
    typeof window !== 'undefined' ? window.location.pathname : '/'

  const [notifOpen, setNotifOpen] = useState(false)
  const notif = useNotifications(Boolean(user) && !loading)

  const [paletteOpen, setPaletteOpen] = useState(false)
  useHotkey('k', 'meta-or-ctrl', useCallback(() => setPaletteOpen(true), []))

  useEffect(() => {
    if (!notifOpen) return
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('[aria-label*="通知"]') && !target.closest('.absolute')) {
        setNotifOpen(false)
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [notifOpen])

  const headerActions = (
    <div className="relative">
      <NotificationBell
        count={notif.summary.total}
        onClick={() => setNotifOpen(!notifOpen)}
      />
      <NotificationPanel
        open={notifOpen}
        summary={notif.summary}
        onNavigate={(path) => {
          setNotifOpen(false)
          void navigate({ to: path })
        }}
      />
    </div>
  )

  return (
    <AuthGuard>
      <AppShell currentPath={currentPath} headerActions={headerActions}>{children}</AppShell>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </AuthGuard>
  )
}
