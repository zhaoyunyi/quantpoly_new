import { cn, transitionClass } from '@qp/ui'
import type { NotificationSummary } from '../../shared/useNotifications'

export interface NotificationPanelProps {
  open: boolean
  summary: NotificationSummary
  onNavigate: (path: string) => void
}

export function NotificationPanel({ open, summary, onNavigate }: NotificationPanelProps) {
  if (!open) return null

  return (
    <div className={cn(
      'absolute right-0 top-full mt-xs w-72 bg-bg-card rounded-md shadow-card border border-secondary-300/20 z-50 overflow-hidden',
      transitionClass,
    )}>
      <div className="px-md py-sm border-b border-secondary-300/10">
        <h3 className="text-body font-medium">通知</h3>
      </div>
      <div className="p-md flex flex-col gap-sm">
        {summary.total === 0 ? (
          <p className="text-caption text-text-muted text-center py-md">暂无待处理通知</p>
        ) : (
          <>
            {summary.alertsOpen > 0 && (
              <button
                type="button"
                onClick={() => onNavigate('/monitor')}
                className="flex items-center justify-between p-sm rounded-sm hover:bg-bg-subtle transition-colors text-left w-full"
              >
                <div>
                  <p className="text-body">未解决告警</p>
                  <p className="text-caption text-text-muted">
                    {summary.alertsCritical > 0 && `${summary.alertsCritical} 条严重 · `}
                    共 {summary.alertsOpen} 条
                  </p>
                </div>
                <span className="text-data-mono text-state-risk font-medium">{summary.alertsOpen}</span>
              </button>
            )}
            {summary.signalsPending > 0 && (
              <button
                type="button"
                onClick={() => onNavigate('/monitor')}
                className="flex items-center justify-between p-sm rounded-sm hover:bg-bg-subtle transition-colors text-left w-full"
              >
                <div>
                  <p className="text-body">待处理信号</p>
                  <p className="text-caption text-text-muted">需要确认执行</p>
                </div>
                <span className="text-data-mono text-state-warning-text font-medium">{summary.signalsPending}</span>
              </button>
            )}
          </>
        )}
      </div>
      <div className="px-md py-sm border-t border-secondary-300/10">
        <button
          type="button"
          onClick={() => onNavigate('/monitor')}
          className="text-caption text-primary-500 hover:text-primary-700 transition-colors"
        >
          查看全部 →
        </button>
      </div>
    </div>
  )
}
