import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import { PublicLayout } from '@qp/shell'
import { useAuth, type AppError } from '@qp/api-client'
import { Button, TextField, useToast } from '@qp/ui'
import { redirectTo } from '../../lib/navigation'

export const Route = createFileRoute('/auth/login')({
  component: LoginPage,
})

function safeNextPath(next: string | null): string | null {
  if (!next) return null
  const trimmed = next.trim()
  if (!trimmed.startsWith('/')) return null
  if (trimmed.startsWith('//')) return null
  return trimmed
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

function passwordStrengthLabel(password: string): '弱' | '中' | '强' {
  const p = password ?? ''
  const hasLetter = /[A-Za-z]/.test(p)
  const hasDigit = /\d/.test(p)
  const hasSymbol = /[^A-Za-z0-9]/.test(p)
  if (p.length >= 12 && hasLetter && hasDigit && hasSymbol) return '强'
  if (p.length >= 8 && hasLetter && hasDigit) return '中'
  return '弱'
}

export function LoginPage() {
  const { login } = useAuth()
  const toast = useToast()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<{
    message: string
    code?: string
  } | null>(null)
  const [emailError, setEmailError] = useState<string>()
  const [passwordError, setPasswordError] = useState<string>()

  const passwordHelp = useMemo(() => {
    if (!password) return '建议使用更长、更难猜的密码。'
    return `密码强度：${passwordStrengthLabel(password)}`
  }, [password])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    const preset = params.get('email')
    if (preset) setEmail(preset)
  }, [])

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFormError(null)
    setEmailError(undefined)
    setPasswordError(undefined)

    const normalizedEmail = email.trim()
    if (!normalizedEmail) {
      setEmailError('请输入邮箱')
      return
    }
    if (!isValidEmail(normalizedEmail)) {
      setEmailError('邮箱格式不正确')
      return
    }
    if (!password) {
      setPasswordError('请输入密码')
      return
    }

    setSubmitting(true)
    try {
      await login(normalizedEmail, password)
      toast.show('登录成功', 'success')

      const next =
        typeof window !== 'undefined'
          ? new URLSearchParams(window.location.search).get('next')
          : null
      const to = safeNextPath(next) ?? '/dashboard'
      redirectTo(to)
    } catch (err) {
      const appErr = err as AppError
      const mapped = mapLoginError(appErr)
      setFormError(mapped)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <PublicLayout>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-xl">
        <h1 className="text-title-section">登录</h1>
        <p className="text-body-secondary mt-xs">
          使用邮箱与密码登录。登录成功后会跳转到你的工作台。
        </p>

        <form className="mt-lg flex flex-col gap-md" onSubmit={onSubmit}>
          {formError && (
            <div
              role="alert"
              className="p-md rounded-sm border border-state-risk/30 bg-bg-subtle text-body text-text-primary"
            >
              <p className="font-medium">登录失败</p>
              <p className="text-body-secondary mt-xs">{formError.message}</p>
              {formError.code === 'EMAIL_NOT_VERIFIED' && (
                <div className="mt-sm flex flex-wrap gap-sm">
                  <a
                    href={`/auth/verify-email?email=${encodeURIComponent(normalizedEmailForLink(email))}`}
                    className="text-primary-700 text-body hover:underline"
                  >
                    去验证邮箱
                  </a>
                  <a
                    href={`/auth/resend-verification?email=${encodeURIComponent(normalizedEmailForLink(email))}`}
                    className="text-primary-700 text-body hover:underline"
                  >
                    重发验证邮件
                  </a>
                </div>
              )}
            </div>
          )}
          <TextField
            label="邮箱"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            autoComplete="email"
            error={emailError}
          />
          <TextField
            label="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
            help={passwordHelp}
            error={passwordError}
          />
          <div className="flex items-center justify-between gap-md">
            <a
              href="/auth/forgot-password"
              className="text-body text-primary-700 hover:underline"
            >
              忘记密码
            </a>
            <Button type="submit" loading={submitting}>
              登录
            </Button>
          </div>

          <p className="text-caption text-text-muted">
            还没有账号？{' '}
            <a href="/auth/register" className="text-primary-700 hover:underline">
              去注册
            </a>
          </p>
        </form>
      </div>
    </PublicLayout>
  )
}

function mapLoginError(error: AppError): { message: string; code?: string } {
  if (error.httpStatus === 401) {
    return { message: '邮箱或密码不正确', code: error.code }
  }
  if (error.code === 'EMAIL_NOT_VERIFIED') {
    return { message: '邮箱未验证，请先完成验证后再登录。', code: error.code }
  }
  if (error.code === 'USER_DISABLED') {
    return { message: '账号已禁用，请联系管理员。', code: error.code }
  }
  return { message: error.message || '登录失败，请稍后再试。', code: error.code }
}

function normalizedEmailForLink(email: string): string {
  return (email ?? '').trim()
}
