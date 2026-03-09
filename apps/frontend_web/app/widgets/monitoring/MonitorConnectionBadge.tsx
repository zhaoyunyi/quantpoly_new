import { StatusPill } from '../dashboard/StatusPill'

export type MonitorConnectionState = 'connecting' | 'connected' | 'degraded' | 'offline'

export function MonitorConnectionBadge({ state }: { state: MonitorConnectionState }) {
  if (state === 'connected') {
    return <StatusPill variant="ok" label="已连接" />
  }
  if (state === 'connecting') {
    return <StatusPill variant="running" label="连接中" />
  }
  if (state === 'degraded') {
    return <StatusPill variant="degraded" label="已降级" />
  }
  return <StatusPill variant="failed" label="离线" />
}

