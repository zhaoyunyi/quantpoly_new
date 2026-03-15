import type { ReactNode } from 'react'
import { cn, transitionClass } from '@qp/ui'

export interface QuickActionItem {
  label: string
  description: string
  href: string
  icon: ReactNode
}

const ACTIONS: QuickActionItem[] = [
  {
    label: '策略管理',
    description: '创建、启停与参数管理',
    href: '/strategies',
    icon: (
      <path
        d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6m-3 7v4m-2-2h4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    ),
  },
  {
    label: '回测中心',
    description: '提交回测并查看结果',
    href: '/backtests',
    icon: (
      <>
        <path
          d="M3 12l2-2m0 0l7-7 7 7m-9-5v12m4-8h4a2 2 0 0 1 2 2v6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <polyline
          points="3,17 8,12 13,16 21,8"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </>
    ),
  },
  {
    label: '交易账户',
    description: '资产、仓位与订单',
    href: '/trading',
    icon: (
      <>
        <rect
          x="3"
          y="5"
          width="18"
          height="14"
          rx="2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M3 10h18M7 15h2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </>
    ),
  },
  {
    label: '实时监控',
    description: '信号、告警与任务状态',
    href: '/monitor',
    icon: (
      <path
        d="M5 12h2l3-7 4 14 3-7h2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
]

export function QuickActions() {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-md">
      {ACTIONS.map((item) => (
        <a
          key={item.href}
          href={item.href}
          className={cn(
            'bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md flex items-start gap-md',
            transitionClass,
            'hover:bg-bg-subtle',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40',
          )}
        >
          <span className="shrink-0 w-9 h-9 rounded-md bg-primary-500/10 text-primary-700 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              {item.icon}
            </svg>
          </span>
          <span className="flex-1 min-w-0">
            <span className="text-body font-medium text-text-primary">
              {item.label}
            </span>
            <span className="block text-body-secondary mt-xs">
              {item.description}
            </span>
          </span>
          <span className="shrink-0 text-text-muted mt-0.5" aria-hidden="true">
            →
          </span>
        </a>
      ))}
    </section>
  )
}
