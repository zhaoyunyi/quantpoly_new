import { createFileRoute } from '@tanstack/react-router'

import { ProtectedLayout } from '../entry_wiring'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})

export function DashboardPage() {
  return (
    <ProtectedLayout>
      <section className="flex flex-col gap-md">
        <h1 className="text-title-page">仪表盘</h1>
        <p className="text-body-secondary">
          当前仅完成认证链路与前端基础设施接线。仪表盘 UI 将在后续任务中逐步落地。
        </p>
      </section>
    </ProtectedLayout>
  )
}

