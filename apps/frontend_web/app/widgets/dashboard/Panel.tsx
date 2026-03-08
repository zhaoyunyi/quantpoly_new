import type { ReactNode } from 'react'
import { cn } from '@qp/ui'

export interface PanelProps {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Panel({ title, subtitle, action, children, className }: PanelProps) {
  return (
    <section
      className={cn(
        'bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md',
        className,
      )}
    >
      <header className="flex items-start justify-between gap-md">
        <div className="flex-1 min-w-0">
          <h2 className="text-title-card">{title}</h2>
          {subtitle && <p className="text-body-secondary mt-xs">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </header>
      <div className="mt-md">{children}</div>
    </section>
  )
}

