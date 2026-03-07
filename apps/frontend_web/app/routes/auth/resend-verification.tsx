import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import type { FormEvent } from 'react'

import { resendVerification, type AppError } from '@qp/api-client'
import { PublicLayout } from '@qp/shell'
import { Button, TextField, useToast } from '@qp/ui'

export const Route = createFileRoute('/auth/resend-verification')({
  component: ResendVerificationPage,
})

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

export function ResendVerificationPage() {
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
      await resendVerification({ email: normalizedEmail })
      toast.show('如果该账户存在，我们已重新发送验证指引。', 'success')
    } catch (err) {
      const appErr = err as AppError
      setFormError(appErr.message || '请求失败，请稍后再试。')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <PublicLayout>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-xl">
        <h1 className="text-title-section">重发验证邮件</h1>
        <p className="text-body-secondary mt-xs">
          为安全起见，无论邮箱是否存在都会返回统一提示。
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
              重发验证指引
            </Button>
          </div>
        </form>
      </div>
    </PublicLayout>
  )
}

