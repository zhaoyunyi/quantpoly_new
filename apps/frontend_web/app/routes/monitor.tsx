import { createFileRoute } from '@tanstack/react-router'
import { useCallback, useEffect, useState } from 'react'

import {
  acknowledgeRiskAlert,
  cancelSignal,
  executeSignal,
  getMonitorSummary,
  getRiskAlerts,
  getSignalsPending,
  processSignal,
  resolveRiskAlert,
  type AppError,
  type MonitorSummary,
  type RiskAlert,
  type TradingSignal,
} from '@qp/api-client'
import { Skeleton, useToast } from '@qp/ui'

import { ProtectedLayout } from '../entry_wiring'
import { useLoadable } from '../shared/useLoadable'
import { useMonitorSocket } from '../shared/useMonitorSocket'
import { DegradedBanner } from '../widgets/dashboard/DegradedBanner'
import { InlineErrorCard } from '../widgets/dashboard/InlineErrorCard'
import { Panel } from '../widgets/dashboard/Panel'
import { AlertList } from '../widgets/monitoring/AlertList'
import { MonitorConnectionBadge } from '../widgets/monitoring/MonitorConnectionBadge'
import { OperationalSummaryBar } from '../widgets/monitoring/OperationalSummaryBar'
import { SignalList } from '../widgets/monitoring/SignalList'

export const Route = createFileRoute('/monitor')({
  component: MonitorPage,
})

export function MonitorPage() {
  const toast = useToast()

  const summary = useLoadable<MonitorSummary>(getMonitorSummary)
  const signalsState = useLoadable<TradingSignal[]>(getSignalsPending)

  const loadAlerts = useCallback(
    () => getRiskAlerts({ unresolvedOnly: true }),
    [],
  )
  const alertsState = useLoadable<RiskAlert[]>(loadAlerts)

  const ws = useMonitorSocket({
    enabled: true,
    channels: ['signals', 'alerts'],
  })

  // WS 降级时，启动轻量 REST 轮询，保持页面可用（联调期）
  useEffect(() => {
    if (ws.connection !== 'degraded') return
    const timer = setInterval(() => {
      void summary.reload()
      void signalsState.reload()
      void alertsState.reload()
    }, 10_000)
    return () => clearInterval(timer)
  }, [ws.connection, summary.reload, signalsState.reload, alertsState.reload])

  const degradedEnabled = !!summary.data?.degraded?.enabled
  const degradedReasons = summary.data?.degraded?.reasons ?? []

  const signals = ws.signals.length > 0 ? ws.signals : signalsState.data ?? []
  const alerts = ws.alerts.length > 0 ? ws.alerts : alertsState.data ?? []

  const [busySignalId, setBusySignalId] = useState<string | null>(null)
  const [busyAlertId, setBusyAlertId] = useState<string | null>(null)

  const onSignalProcess = useCallback(
    async (signalId: string) => {
      setBusySignalId(signalId)
      try {
        await processSignal(signalId)
        toast.show('已处理信号', 'success')
        await signalsState.reload()
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '处理失败', 'error')
      } finally {
        setBusySignalId(null)
      }
    },
    [signalsState, toast],
  )

  const onSignalExecute = useCallback(
    async (signalId: string) => {
      setBusySignalId(signalId)
      try {
        await executeSignal(signalId)
        toast.show('已提交执行', 'success')
        await signalsState.reload()
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '执行失败', 'error')
      } finally {
        setBusySignalId(null)
      }
    },
    [signalsState, toast],
  )

  const onSignalCancel = useCallback(
    async (signalId: string) => {
      setBusySignalId(signalId)
      try {
        await cancelSignal(signalId)
        toast.show('已取消信号', 'success')
        await signalsState.reload()
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '取消失败', 'error')
      } finally {
        setBusySignalId(null)
      }
    },
    [signalsState, toast],
  )

  const onAlertAcknowledge = useCallback(
    async (alertId: string) => {
      setBusyAlertId(alertId)
      try {
        await acknowledgeRiskAlert(alertId)
        toast.show('已确认告警', 'success')
        await alertsState.reload()
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '确认失败', 'error')
      } finally {
        setBusyAlertId(null)
      }
    },
    [alertsState, toast],
  )

  const onAlertResolve = useCallback(
    async (alertId: string) => {
      setBusyAlertId(alertId)
      try {
        await resolveRiskAlert(alertId)
        toast.show('已解决告警', 'success')
        await alertsState.reload()
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '解决失败', 'error')
      } finally {
        setBusyAlertId(null)
      }
    },
    [alertsState, toast],
  )

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <h1 className="text-title-page">实时监控</h1>
            <p className="text-body-secondary mt-xs">
              通过 WebSocket 订阅 signals/alerts，并在断线时自动降级到 REST 轮询。
            </p>
          </div>
          <div className="shrink-0">
            <MonitorConnectionBadge state={ws.connection} />
          </div>
        </header>

        {degradedEnabled && <DegradedBanner reasons={degradedReasons} />}

        <section className="grid grid-cols-1 xl:grid-cols-2 gap-md">
          <Panel title="Signals" subtitle="待处理信号（/signals/pending + /ws/monitor）">
            {signalsState.loading ? (
              <div className="grid grid-cols-2 gap-md">
                {Array.from({ length: 6 }).map((_, idx) => (
                  <div key={idx} className="flex flex-col gap-xs">
                    <Skeleton width="70%" height="12px" />
                    <Skeleton width="60%" height="18px" />
                  </div>
                ))}
              </div>
            ) : signalsState.error ? (
              <InlineErrorCard
                title="Signals 加载失败"
                message={signalsState.error.message || '无法获取 signals。'}
                onRetry={() => void signalsState.reload()}
              />
            ) : (
              <SignalList
                signals={signals}
                busySignalId={busySignalId}
                onProcess={onSignalProcess}
                onExecute={onSignalExecute}
                onCancel={onSignalCancel}
              />
            )}
          </Panel>

          <Panel title="Alerts" subtitle="未解决告警（/risk/alerts?unresolvedOnly=true + /ws/monitor）">
            {alertsState.loading ? (
              <div className="grid grid-cols-2 gap-md">
                {Array.from({ length: 6 }).map((_, idx) => (
                  <div key={idx} className="flex flex-col gap-xs">
                    <Skeleton width="70%" height="12px" />
                    <Skeleton width="60%" height="18px" />
                  </div>
                ))}
              </div>
            ) : alertsState.error ? (
              <InlineErrorCard
                title="Alerts 加载失败"
                message={alertsState.error.message || '无法获取 alerts。'}
                onRetry={() => void alertsState.reload()}
              />
            ) : (
              <AlertList
                alerts={alerts}
                busyAlertId={busyAlertId}
                onAcknowledge={onAlertAcknowledge}
                onResolve={onAlertResolve}
              />
            )}
          </Panel>
        </section>

        <Panel title="Operational Summary" subtitle="运营摘要（/monitor/summary）">
          {summary.loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="flex flex-col gap-xs">
                  <Skeleton width="70%" height="12px" />
                  <Skeleton width="60%" height="18px" />
                </div>
              ))}
            </div>
          ) : summary.error ? (
            <InlineErrorCard
              title="摘要加载失败"
              message={summary.error.message || '无法获取监控摘要。'}
              onRetry={() => void summary.reload()}
            />
          ) : summary.data ? (
            <OperationalSummaryBar summary={summary.data} />
          ) : (
            <InlineErrorCard
              title="摘要为空"
              message="未获取到摘要数据。"
              onRetry={() => void summary.reload()}
            />
          )}
        </Panel>
      </div>
    </ProtectedLayout>
  )
}
