import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'

import { requestPasswordReset, type AppError } from '@qp/api-client'
import { PublicLayout } from '@qp/shell'
import { Button, TextField, useToast } from '@qp/ui'

export const Route = createFileRoute('/auth/forgot-password')({
  component: ForgotPasswordPage,
})

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

export function ForgotPasswordPage() {
  const toast = useToast()
  const [email, setEmail] = useState('')
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
      await requestPasswordReset({ email: normalizedEmail })
      toast.show('如果该账户存在，我们已发送重置指引。', 'success')
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
        <h1 className="text-title-section">找回密码</h1>
        <p className="text-body-secondary mt-xs">
          输入邮箱后，我们会发送重置密码指引（为安全起见，不会透露账户是否存在）。
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
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setEmail(e.target.value)
            }
            placeholder="name@example.com"
            autoComplete="email"
            error={emailError}
          />

          <div className="flex items-center justify-between gap-md">
            <a href="/auth/login" className="text-body text-primary-700 hover:underline">
              返回登录
            </a>
            <Button type="submit" loading={submitting}>
              发送重置指引
            </Button>
          </div>
        </form>
      </div>
    </PublicLayout>
  )
}
