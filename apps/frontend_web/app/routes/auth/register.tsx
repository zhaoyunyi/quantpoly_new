import { createFileRoute } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'

import { register, type AppError } from '@qp/api-client'
import { PublicLayout } from '@qp/shell'
import { Button, TextField, useToast } from '@qp/ui'
import { redirectTo } from '../../lib/navigation'

export const Route = createFileRoute('/auth/register')({
  component: RegisterPage,
})

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

function mapRegisterError(error: AppError): string {
  if (error.httpStatus === 409) return '该邮箱已注册，请直接登录。'
  if (error.httpStatus === 400) return '密码强度不足，请尝试更强的密码。'
  return error.message || '注册失败，请稍后再试。'
}

export function RegisterPage() {
  const toast = useToast()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string>()
  const [emailError, setEmailError] = useState<string>()
  const [passwordError, setPasswordError] = useState<string>()

  const passwordHelp = useMemo(() => {
    if (!password) return '建议使用更长、更难猜的密码。'
    return `密码强度：${passwordStrengthLabel(password)}`
  }, [password])

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFormError(undefined)
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
      await register({ email: normalizedEmail, password })
      toast.show('注册成功，请先验证邮箱后再登录。', 'success')
      redirectTo(`/auth/verify-email?email=${encodeURIComponent(normalizedEmail)}`)
    } catch (err) {
      const appErr = err as AppError
      setFormError(mapRegisterError(appErr))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <PublicLayout>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-xl">
        <h1 className="text-title-section">注册</h1>
        <p className="text-body-secondary mt-xs">
          创建账号后需要完成邮箱验证才能登录。
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

          <TextField
            label="密码"
            value={password}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setPassword(e.target.value)
            }
            type="password"
            autoComplete="new-password"
            help={passwordHelp}
            error={passwordError}
          />

          <div className="flex items-center justify-between gap-md">
            <a href="/auth/login" className="text-body text-primary-700 hover:underline">
              已有账号？去登录
            </a>
            <Button type="submit" loading={submitting}>
              注册
            </Button>
          </div>
        </form>
      </div>
    </PublicLayout>
  )
}
