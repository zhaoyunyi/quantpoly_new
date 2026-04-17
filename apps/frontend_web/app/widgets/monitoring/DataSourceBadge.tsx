export interface DataSourceBadgeProps {
  source: 'ws' | 'rest'
}

export function DataSourceBadge({ source }: DataSourceBadgeProps) {
  return (
    <span className="text-[11px] px-xs py-0.5 rounded-sm bg-bg-subtle border border-secondary-300/20 text-text-muted font-medium">
      {source === 'ws' ? 'WebSocket' : 'REST'}
    </span>
  )
}
