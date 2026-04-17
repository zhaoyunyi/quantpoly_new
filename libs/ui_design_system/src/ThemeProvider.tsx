import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  theme: Theme
  resolved: 'light' | 'dark'
  setTheme: (t: Theme) => void
}

const STORAGE_KEY = 'qp-theme'

const ThemeContext = createContext<ThemeContextValue | null>(null)

function getThemeMediaQuery(): MediaQueryList | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return null
  }
  return window.matchMedia('(prefers-color-scheme: dark)')
}

function getSystemTheme(): 'light' | 'dark' {
  return getThemeMediaQuery()?.matches ? 'dark' : 'light'
}

function resolve(theme: Theme): 'light' | 'dark' {
  return theme === 'system' ? getSystemTheme() : theme
}

function applyClass(resolved: 'light' | 'dark') {
  const root = document.documentElement
  root.classList.toggle('dark', resolved === 'dark')
}

export function ThemeProvider({ children, defaultTheme = 'system' }: { children: ReactNode; defaultTheme?: Theme }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return defaultTheme
    return (localStorage.getItem(STORAGE_KEY) as Theme) ?? defaultTheme
  })

  const [resolved, setResolved] = useState<'light' | 'dark'>(() => resolve(theme))

  const setTheme = (t: Theme) => {
    localStorage.setItem(STORAGE_KEY, t)
    setThemeState(t)
  }

  useEffect(() => {
    const r = resolve(theme)
    setResolved(r)
    applyClass(r)
  }, [theme])

  useEffect(() => {
    if (theme !== 'system') return
    const mq = getThemeMediaQuery()
    if (!mq) return
    const handler = () => {
      const r = resolve('system')
      setResolved(r)
      applyClass(r)
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  return (
    <ThemeContext value={{ theme, resolved, setTheme }}>
      {children}
    </ThemeContext>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
