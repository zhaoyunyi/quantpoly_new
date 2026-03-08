import { cn, transitionClass } from '@qp/ui'

export type StatusPillVariant = 'ok' | 'running' | 'failed' | 'degraded'

const variantClasses: Record<StatusPillVariant, string> = {
  ok: 'border-secondary-300/20 bg-bg-card text-text-secondary',
  running: 'border-primary-500/30 bg-primary-500/10 text-primary-700',
  failed: 'border-state-risk/30 bg-state-risk/10 text-state-risk',
  degraded: 'border-state-risk/30 bg-bg-subtle text-state-risk',
}

const variantLabel: Record<StatusPillVariant, string> = {
  ok: 'OK',
  running: 'RUNNING',
  failed: 'FAILED',
  degraded: 'DEGRADED',
}

export interface StatusPillProps {
  variant: StatusPillVariant
  label?: string
  className?: string
}

export function StatusPill({ variant, label, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-sm py-xs rounded-sm border text-caption',
        transitionClass,
        variantClasses[variant],
        className,
      )}
    >
      {label ?? variantLabel[variant]}
    </span>
  )
}

