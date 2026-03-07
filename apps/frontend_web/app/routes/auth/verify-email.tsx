import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import type { FormEvent } from 'react'

import { verifyEmail, type AppError } from '@qp/api-client'
import { PublicLayout } from '@qp/shell'
import { Button, TextField, useToast } from '@qp/ui'
import { redirectTo } from '../../lib/navigation'

export const Route = createFileRoute('/auth/verify-email')({
  component: VerifyEmailPage,
})

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

function mapVerifyError(error: AppError): string {
  if (error.httpStatus === 404) return '未找到该账户，请确认邮箱是否正确。'
  return error.message || '验证失败，请稍后再试。'
}

export function VerifyEmailPage() {
  const toast = useToast()

  const [email, setEmail] = useState(() => {
    if (typeof window === 'undefined') return ''
    return new URLSearchParams(window.location.search).get('email') ?? ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [emailError, setEmailError] = useState<string>()
  const [formError, setFormError] = useState<string>()

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setEmailError(undefined)
    setFormError(undefined)

    const normalizedEmail = email.trim()
    if (!normalizedEmail) {
      setEmailError('请输入邮箱')
      return
    }
    if (!isValidEmail(normalizedEmail)) {
      setEmailError('邮箱格式不正确')
      return
    }

    setSubmitting(true)
    try {
      await verifyEmail({ email: normalizedEmail })
      toast.show('邮箱已验证，可以登录。', 'success')
      redirectTo(`/auth/login?email=${encodeURIComponent(normalizedEmail)}`)
    } catch (err) {
      const appErr = err as AppError
      setFormError(mapVerifyError(appErr))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <PublicLayout>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-xl">
        <h1 className="text-title-section">验证邮箱</h1>
        <p className="text-body-secondary mt-xs">
          开发模式下可通过邮箱直接完成验证（真实邮件流程后续接入）。
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
            label="邮箱"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            autoComplete="email"
            error={emailError}
          />

          <div className="flex items-center justify-between gap-md">
            <a href="/auth/login" className="text-body text-primary-700 hover:underline">
              返回登录
            </a>
            <Button type="submit" loading={submitting}>
              验证邮箱
            </Button>
          </div>
        </form>
      </div>
    </PublicLayout>
  )
}

