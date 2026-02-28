/**
 * Frontend API Client — React Hooks
 *
 * 提供 useAuth 等便捷 hooks 供组件使用。
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import type { UserProfile } from './endpoints'
import { getMe, login as apiLogin, logout as apiLogout } from './endpoints'
import type { AppError } from './errors'
import { isAuthError } from './errors'

/* ─── Auth Context ─── */

export interface AuthState {
  /** 当前登录用户，null 表示未登录 */
  user: UserProfile | null
  /** 是否正在加载用户信息 */
  loading: boolean
  /** 加载过程中的错误 */
  error: AppError | null
  /** 登录 */
  login: (email: string, password: string) => Promise<void>
  /** 登出 */
  logout: () => Promise<void>
  /** 重新刷新用户信息 */
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export interface AuthProviderProps {
  children: ReactNode
  /** 首屏注入的用户信息（通常来自 SSR） */
  initialUser?: UserProfile | null
  /** 首屏是否已完成认证状态解析 */
  initialResolved?: boolean
}

export function AuthProvider({
  children,
  initialUser = null,
  initialResolved = false,
}: AuthProviderProps) {
  const [user, setUser] = useState<UserProfile | null>(
    initialResolved ? (initialUser ?? null) : null,
  )
  const [loading, setLoading] = useState(!initialResolved)
  const [error, setError] = useState<AppError | null>(null)

  const loadUser = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true)
    setError(null)
    try {
      const me = await getMe()
      setUser(me)
    } catch (err) {
      const appErr = err as AppError
      if (isAuthError(appErr)) {
        // 未登录是正常状态，不设 error
        setUser(null)
      } else {
        setError(appErr)
        setUser(null)
      }
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    await loadUser()
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      await apiLogin({ email, password })
      await loadUser()
    },
    [loadUser],
  )

  const logout = useCallback(async () => {
    await apiLogout()
    setUser(null)
  }, [])

  useEffect(() => {
    if (initialResolved) return
    void loadUser()
  }, [initialResolved, loadUser])

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  )
}

/** 获取认证状态。必须在 AuthProvider 内使用。 */
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth 必须在 <AuthProvider> 内使用')
  }
  return ctx
}
