import { cn, transitionClass } from '@qp/ui'

export interface NotificationBellProps {
  count: number
  onClick: () => void
}

export function NotificationBell({ count, onClick }: NotificationBellProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-bg-subtle',
        transitionClass,
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40',
      )}
      aria-label={count > 0 ? `${count} 条未读通知` : '通知'}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M18 8A6 6 0 1 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M13.73 21a2 2 0 0 1-3.46 0"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {count > 0 && (
        <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-state-risk text-[10px] font-medium text-white leading-none">
          {count > 99 ? '99+' : count}
        </span>
      )}
    </button>
  )
}
