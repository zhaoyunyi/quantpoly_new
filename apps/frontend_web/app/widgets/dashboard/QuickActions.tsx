import { cn, transitionClass } from '@qp/ui'
import { ClipboardPlus, TrendingUp, CreditCard, Activity, type LucideIcon } from 'lucide-react'

interface QuickActionItem {
  label: string
  description: string
  href: string
  icon: LucideIcon
}

const ACTIONS: QuickActionItem[] = [
  {
    label: '策略管理',
    description: '创建、启停与参数管理',
    href: '/strategies',
    icon: ClipboardPlus,
  },
  {
    label: '回测中心',
    description: '提交回测并查看结果',
    href: '/backtests',
    icon: TrendingUp,
  },
  {
    label: '交易账户',
    description: '资产、仓位与订单',
    href: '/trading',
    icon: CreditCard,
  },
  {
    label: '实时监控',
    description: '信号、告警与任务状态',
    href: '/monitor',
    icon: Activity,
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
            <item.icon className="size-5" aria-hidden="true" />
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
