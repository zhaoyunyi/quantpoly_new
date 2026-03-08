import { Button, cn, transitionClass } from '@qp/ui'

export interface InlineErrorCardProps {
  title: string
  message: string
  onRetry?: () => void
  className?: string
}

export function InlineErrorCard({
  title,
  message,
  onRetry,
  className,
}: InlineErrorCardProps) {
  return (
    <div
      role="alert"
      className={cn(
        'bg-bg-card rounded-md shadow-card border border-state-risk/30 p-md',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-md">
        <div className="flex-1 min-w-0">
          <p className="text-body font-medium text-text-primary">{title}</p>
          <p className="text-body-secondary mt-xs break-words">{message}</p>
        </div>
        {onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry}>
            重试
          </Button>
        )}
      </div>
      <p className={cn('text-caption mt-sm state-risk', transitionClass)}>
        error
      </p>
    </div>
  )
}

