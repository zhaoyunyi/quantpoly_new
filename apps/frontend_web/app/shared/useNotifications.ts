import { usePolling } from './usePolling'
import { getRiskAlertStats, getSignalsDashboard } from '@qp/api-client'
import type { RiskAlertStats, SignalsDashboard } from '@qp/api-client'
import { useCallback, useMemo } from 'react'

export interface NotificationSummary {
  alertsOpen: number
  alertsCritical: number
  signalsPending: number
  total: number
}

export function useNotifications(enabled: boolean) {
  const loadAlertStats = useCallback(() => getRiskAlertStats(), [])
  const loadSignals = useCallback(() => getSignalsDashboard(), [])

  const alerts = usePolling<RiskAlertStats>(loadAlertStats, 30_000, enabled)
  const signals = usePolling<SignalsDashboard>(loadSignals, 30_000, enabled)

  const summary: NotificationSummary = useMemo(() => {
    const alertsOpen = alerts.data?.open ?? 0
    const alertsCritical = alerts.data?.bySeverity?.critical ?? 0
    const signalsPending = signals.data?.pending ?? 0
    return {
      alertsOpen,
      alertsCritical,
      signalsPending,
      total: alertsOpen + signalsPending,
    }
  }, [alerts.data, signals.data])

  return {
    summary,
    loading: alerts.loading || signals.loading,
    reload: async () => {
      await Promise.all([alerts.reload(), signals.reload()])
    },
  }
}
