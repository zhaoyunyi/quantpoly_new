import type { ReactNode } from 'react'
import { cn, transitionClass } from '@qp/ui'

export type KpiTone = 'default' | 'up' | 'down' | 'risk'

const toneValueClass: Record<KpiTone, string> = {
  default: 'text-data-primary',
  up: 'text-data-primary state-up',
  down: 'text-data-primary state-down',
  risk: 'text-data-primary state-risk',
}

export interface KpiCardProps {
  title: string
  value: ReactNode
  subvalue?: ReactNode
  hint?: ReactNode
  tone?: KpiTone
  href?: string
}

export function KpiCard({
  title,
  value,
  subvalue,
  hint,
  tone = 'default',
  href,
}: KpiCardProps) {
  const content = (
    <div
      className={cn(
        'bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md',
        transitionClass,
        href && 'hover:bg-bg-subtle',
      )}
    >
      <p className="text-caption">{title}</p>
      <div className="mt-sm flex items-baseline justify-between gap-md">
        <div className={toneValueClass[tone]} data-mono>
          {value}
        </div>
        {subvalue && (
          <div className="text-data-secondary text-right" data-mono>
            {subvalue}
          </div>
        )}
      </div>
      {hint && <p className="text-body-secondary mt-sm">{hint}</p>}
    </div>
  )

  if (href) {
    return (
      <a href={href} className="block">
        {content}
      </a>
    )
  }

  return content
}

