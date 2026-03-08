import { cn } from '@qp/ui'

export interface DegradedBannerProps {
  reasons: string[]
  className?: string
}

export function DegradedBanner({ reasons, className }: DegradedBannerProps) {
  if (!reasons.length) return null

  return (
    <div
      role="alert"
      className={cn(
        'p-md rounded-md border border-state-risk/30 bg-bg-subtle',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-md">
        <div className="flex-1">
          <p className="text-body font-medium text-text-primary">
            部分数据源已降级
          </p>
          <p className="text-body-secondary mt-xs">
            当前仅展示可用数据。请稍后重试或检查后端服务状态。
          </p>
        </div>
        <span
          className="shrink-0 text-caption state-risk"
          aria-label="降级提示"
        >
          degraded
        </span>
      </div>

      <div className="mt-sm flex flex-wrap gap-sm">
        {reasons.map((reason) => (
          <span
            key={reason}
            className="px-sm py-xs rounded-sm bg-bg-card border border-secondary-300/20 text-data-mono"
          >
            {reason}
          </span>
        ))}
      </div>
    </div>
  )
}

