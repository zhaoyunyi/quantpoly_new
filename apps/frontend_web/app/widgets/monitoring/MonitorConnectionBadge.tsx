import { Button } from '@qp/ui'

import { StatusPill } from '../dashboard/StatusPill'

export type MonitorConnectionState = 'connecting' | 'connected' | 'degraded' | 'offline'

export function MonitorConnectionBadge({
  state,
  onReconnect,
}: {
  state: MonitorConnectionState
  onReconnect?: () => void
}) {
  if (state === 'connected') {
    return <StatusPill variant="ok" label="已连接" />
  }
  if (state === 'connecting') {
    return <StatusPill variant="running" label="连接中" />
  }
  if (state === 'degraded') {
    return (
      <span className="inline-flex items-center gap-xs">
        <StatusPill variant="degraded" label="已降级" />
        {onReconnect && (
          <Button variant="ghost" size="sm" onClick={onReconnect}>
            重新连接
          </Button>
        )}
      </span>
    )
  }
  return <StatusPill variant="failed" label="离线" />
}

