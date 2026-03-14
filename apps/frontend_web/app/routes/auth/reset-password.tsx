import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'

import { confirmPasswordReset, type AppError } from '@qp/api-client'
import { PublicLayout } from '@qp/shell'
import { Button, TextField, useToast } from '@qp/ui'

export const Route = createFileRoute('/auth/reset-password')({
  component: ResetPasswordPage,
})

function passwordStrengthLabel(password: string): '弱' | '中' | '强' {
  const p = password ?? ''
  const hasLetter = /[A-Za-z]/.test(p)
  const hasDigit = /\d/.test(p)
  const hasSymbol = /[^A-Za-z0-9]/.test(p)
  if (p.length >= 12 && hasLetter && hasDigit && hasSymbol) return '强'
  if (p.length >= 8 && hasLetter && hasDigit) return '中'
  return '弱'
}

function mapResetError(error: AppError): string {
  if (error.code === 'HTTP_ERROR' && /reset token/i.test(error.message || '')) {
    return '重置链接无效或已过期'
  }
  return error.message || '重置失败，请稍后再试。'
}

export function ResetPasswordPage() {
  const toast = useToast()

  const [token, setToken] = useState(() => {
    if (typeof window === 'undefined') return ''
    return new URLSearchParams(window.location.search).get('token') ?? ''
  })
  const [newPassword, setNewPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string>()
  const [tokenError, setTokenError] = useState<string>()
  const [passwordError, setPasswordError] = useState<string>()

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFormError(undefined)
    setTokenError(undefined)
    setPasswordError(undefined)

    const normalizedToken = token.trim()
    if (!normalizedToken) {
      setTokenError('缺少重置令牌')
      return
    }
    if (!newPassword) {
      setPasswordError('请输入新密码')
      return
    }

    setSubmitting(true)
    try {
      await confirmPasswordReset({ token: normalizedToken, newPassword })
      toast.show('密码已重置，请使用新密码重新登录。', 'success')
    } catch (err) {
      const appErr = err as AppError
      setFormError(mapResetError(appErr))
    } finally {
      setSubmitting(false)
    }
  }

  const passwordHelp = newPassword
    ? `密码强度：${passwordStrengthLabel(newPassword)}`
    : '建议使用更长、更难猜的密码。'

  return (
    <PublicLayout>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-xl">
        <h1 className="text-title-section">重置密码</h1>
        <p className="text-body-secondary mt-xs">
          请设置新密码。完成后可使用新密码重新登录。
        </p>

        <form className="mt-lg flex flex-col gap-md" onSubmit={onSubmit}>
          {formError && (
            <div
              role="alert"
              className="p-md rounded-sm border border-state-risk/30 bg-bg-subtle text-body text-text-primary"
            >
              {formError}
            </div>
          )}

          <TextField
            label="重置令牌"
            value={token}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setToken(e.target.value)
            }
            placeholder="token"
            error={tokenError}
          />

          <TextField
            label="新密码"
            value={newPassword}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setNewPassword(e.target.value)
            }
            type="password"
            autoComplete="new-password"
            help={passwordHelp}
            error={passwordError}
          />

          <div className="flex items-center justify-between gap-md">
            <a href="/auth/login" className="text-body text-primary-700 hover:underline">
              返回登录
            </a>
            <Button type="submit" loading={submitting}>
              重置密码
            </Button>
          </div>
        </form>
      </div>
    </PublicLayout>
  )
}
