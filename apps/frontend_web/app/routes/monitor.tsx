import { createFileRoute } from '@tanstack/react-router'
import { useCallback, useEffect, useState } from 'react'

import {
  acknowledgeRiskAlert,
  batchAcknowledgeRiskAlerts,
  batchCancelSignals,
  batchExecuteSignals,
  cancelSignal,
  executeSignal,
  getMonitorSummary,
  getRiskAlertStats,
  getRiskAlerts,
  getSignals,
  getSignalsPending,
  processSignal,
  resolveRiskAlert,
  searchSignals,
  type AppError,
  type MonitorSummary,
  type RiskAlert,
  type RiskAlertStats,
  type TradingSignal,
} from '@qp/api-client'
import { Button, Skeleton, TextField, useToast } from '@qp/ui'

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

type SignalSourceMode = 'pending' | 'list' | 'search'
const EMPTY_SIGNALS: TradingSignal[] = []
const EMPTY_ALERTS: RiskAlert[] = []

export function MonitorPage() {
  const toast = useToast()

  const summary = useLoadable<MonitorSummary>(getMonitorSummary)
  const alertStats = useLoadable<RiskAlertStats>(getRiskAlertStats)

  const [signalSource, setSignalSource] = useState<SignalSourceMode>('pending')
  const [keywordInput, setKeywordInput] = useState('')
  const [statusInput, setStatusInput] = useState('')
  const [signalKeyword, setSignalKeyword] = useState('')
  const [signalStatus, setSignalStatus] = useState('')

  const loadSignals = useCallback(() => {
    if (signalSource === 'pending') {
      return getSignalsPending()
    }

    const params = {
      keyword: signalKeyword || undefined,
      status: signalStatus || undefined,
    }
    if (signalSource === 'search') {
      return searchSignals(params)
    }
    return getSignals(params)
  }, [signalSource, signalKeyword, signalStatus])

  const signalsState = useLoadable<TradingSignal[]>(loadSignals)

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
      void alertStats.reload()
    }, 10_000)
    return () => clearInterval(timer)
  }, [ws.connection, summary.reload, signalsState.reload, alertsState.reload, alertStats.reload])

  const degradedEnabled = !!summary.data?.degraded?.enabled
  const degradedReasons = summary.data?.degraded?.reasons ?? []

  const useLiveSignals = signalSource === 'pending'
  const signals = useLiveSignals && ws.signals.length > 0 ? ws.signals : signalsState.data ?? EMPTY_SIGNALS
  const alerts = ws.alerts.length > 0 ? ws.alerts : alertsState.data ?? EMPTY_ALERTS

  const [busySignalId, setBusySignalId] = useState<string | null>(null)
  const [busyAlertId, setBusyAlertId] = useState<string | null>(null)
  const [busySignalBatchAction, setBusySignalBatchAction] = useState<'execute' | 'cancel' | null>(null)
  const [busyAlertBatchAck, setBusyAlertBatchAck] = useState(false)

  const [selectedSignalIds, setSelectedSignalIds] = useState<string[]>([])
  const [selectedAlertIds, setSelectedAlertIds] = useState<string[]>([])

  useEffect(() => {
    setSelectedSignalIds((prev) => {
      const next = prev.filter((id) => signals.some((item) => item.id === id))
      const unchanged = next.length === prev.length && next.every((id, idx) => id === prev[idx])
      return unchanged ? prev : next
    })
  }, [signals])

  useEffect(() => {
    setSelectedAlertIds((prev) => {
      const next = prev.filter((id) => alerts.some((item) => item.id === id))
      const unchanged = next.length === prev.length && next.every((id, idx) => id === prev[idx])
      return unchanged ? prev : next
    })
  }, [alerts])

  const onApplySignalFilters = useCallback(() => {
    setSignalKeyword(keywordInput.trim())
    setSignalStatus(statusInput.trim())
  }, [keywordInput, statusInput])

  const onResetSignalFilters = useCallback(() => {
    setKeywordInput('')
    setStatusInput('')
    setSignalKeyword('')
    setSignalStatus('')
  }, [])

  const onToggleSignal = useCallback((signalId: string, selected: boolean) => {
    setSelectedSignalIds((prev) => {
      if (selected) {
        if (prev.includes(signalId)) return prev
        return [...prev, signalId]
      }
      return prev.filter((item) => item !== signalId)
    })
  }, [])

  const onToggleAllSignals = useCallback(
    (selected: boolean) => {
      setSelectedSignalIds(selected ? signals.map((item) => item.id) : [])
    },
    [signals],
  )

  const onToggleAlert = useCallback((alertId: string, selected: boolean) => {
    setSelectedAlertIds((prev) => {
      if (selected) {
        if (prev.includes(alertId)) return prev
        return [...prev, alertId]
      }
      return prev.filter((item) => item !== alertId)
    })
  }, [])

  const onToggleAllAlerts = useCallback(
    (selected: boolean) => {
      setSelectedAlertIds(selected ? alerts.map((item) => item.id) : [])
    },
    [alerts],
  )

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

  const onBatchSignalExecute = useCallback(async () => {
    if (selectedSignalIds.length === 0) return
    setBusySignalBatchAction('execute')
    try {
      const result = await batchExecuteSignals(selectedSignalIds)
      toast.show(`批量执行完成：${result.executed}/${result.total}`, 'success')
      setSelectedSignalIds([])
      await signalsState.reload()
    } catch (err) {
      const appErr = err as AppError
      toast.show(appErr.message || '批量执行失败', 'error')
    } finally {
      setBusySignalBatchAction(null)
    }
  }, [selectedSignalIds, signalsState, toast])

  const onBatchSignalCancel = useCallback(async () => {
    if (selectedSignalIds.length === 0) return
    setBusySignalBatchAction('cancel')
    try {
      const result = await batchCancelSignals(selectedSignalIds)
      toast.show(`批量取消完成：${result.cancelled}/${result.total}`, 'success')
      setSelectedSignalIds([])
      await signalsState.reload()
    } catch (err) {
      const appErr = err as AppError
      toast.show(appErr.message || '批量取消失败', 'error')
    } finally {
      setBusySignalBatchAction(null)
    }
  }, [selectedSignalIds, signalsState, toast])

  const onAlertAcknowledge = useCallback(
    async (alertId: string) => {
      setBusyAlertId(alertId)
      try {
        await acknowledgeRiskAlert(alertId)
        toast.show('已确认告警', 'success')
        await Promise.all([alertsState.reload(), alertStats.reload()])
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '确认失败', 'error')
      } finally {
        setBusyAlertId(null)
      }
    },
    [alertsState, alertStats, toast],
  )

  const onAlertResolve = useCallback(
    async (alertId: string) => {
      setBusyAlertId(alertId)
      try {
        await resolveRiskAlert(alertId)
        toast.show('已解决告警', 'success')
        await Promise.all([alertsState.reload(), alertStats.reload()])
      } catch (err) {
        const appErr = err as AppError
        toast.show(appErr.message || '解决失败', 'error')
      } finally {
        setBusyAlertId(null)
      }
    },
    [alertsState, alertStats, toast],
  )

  const onBatchAlertAcknowledge = useCallback(async () => {
    if (selectedAlertIds.length === 0) return
    setBusyAlertBatchAck(true)
    try {
      const result = await batchAcknowledgeRiskAlerts(selectedAlertIds)
      toast.show(`已批量确认 ${result.affected} 条告警`, 'success')
      setSelectedAlertIds([])
      await Promise.all([alertsState.reload(), alertStats.reload()])
    } catch (err) {
      const appErr = err as AppError
      toast.show(appErr.message || '批量确认失败', 'error')
    } finally {
      setBusyAlertBatchAck(false)
    }
  }, [selectedAlertIds, alertsState, alertStats, toast])

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
          <Panel title="Signals" subtitle="待处理与检索信号（/signals、/signals/search、/signals/pending）">
            <div className="mb-md flex flex-col gap-sm">
              <div className="flex flex-wrap items-center gap-xs">
                <Button
                  variant={signalSource === 'pending' ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setSignalSource('pending')}
                >
                  待处理信号
                </Button>
                <Button
                  variant={signalSource === 'list' ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setSignalSource('list')}
                >
                  全部信号
                </Button>
                <Button
                  variant={signalSource === 'search' ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setSignalSource('search')}
                >
                  搜索信号
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto_auto] gap-sm items-end">
                <TextField
                  label="关键词"
                  value={keywordInput}
                  onChange={(event) => setKeywordInput(event.currentTarget.value)}
                  placeholder="例如：AAPL / moving_average"
                />
                <TextField
                  label="状态"
                  value={statusInput}
                  onChange={(event) => setStatusInput(event.currentTarget.value)}
                  placeholder="例如：pending / executed / cancelled"
                />
                <Button size="sm" onClick={onApplySignalFilters}>
                  应用筛选
                </Button>
                <Button variant="secondary" size="sm" onClick={onResetSignalFilters}>
                  清空筛选
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-sm">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={selectedSignalIds.length === 0 || busySignalBatchAction !== null}
                  loading={busySignalBatchAction === 'execute'}
                  onClick={onBatchSignalExecute}
                >
                  批量执行
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={selectedSignalIds.length === 0 || busySignalBatchAction !== null}
                  loading={busySignalBatchAction === 'cancel'}
                  onClick={onBatchSignalCancel}
                >
                  批量取消
                </Button>
                <span className="text-caption text-text-muted">已选 {selectedSignalIds.length} 项</span>
              </div>
            </div>

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
                selectedSignalIds={selectedSignalIds}
                onToggleSignal={onToggleSignal}
                onToggleAllSignals={onToggleAllSignals}
                onProcess={onSignalProcess}
                onExecute={onSignalExecute}
                onCancel={onSignalCancel}
              />
            )}
          </Panel>

          <Panel title="Alerts" subtitle="未解决告警与统计（/risk/alerts、/risk/alerts/stats）">
            <AlertStatsGrid
              state={alertStats}
              onRetry={() => void alertStats.reload()}
            />

            <div className="mb-md flex flex-wrap items-center gap-sm">
              <Button
                variant="secondary"
                size="sm"
                disabled={selectedAlertIds.length === 0 || busyAlertBatchAck}
                loading={busyAlertBatchAck}
                onClick={onBatchAlertAcknowledge}
              >
                批量确认告警
              </Button>
              <span className="text-caption text-text-muted">已选 {selectedAlertIds.length} 项</span>
            </div>

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
                selectedAlertIds={selectedAlertIds}
                onToggleAlert={onToggleAlert}
                onToggleAllAlerts={onToggleAllAlerts}
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

function AlertStatsGrid({
  state,
  onRetry,
}: {
  state: {
    loading: boolean
    data: RiskAlertStats | null
    error: AppError | null
  }
  onRetry: () => void
}) {
  if (state.loading) {
    return (
      <div className="mb-md grid grid-cols-2 lg:grid-cols-4 gap-sm">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div key={idx} className="flex flex-col gap-xs">
            <Skeleton width="70%" height="12px" />
            <Skeleton width="60%" height="18px" />
          </div>
        ))}
      </div>
    )
  }

  if (state.error) {
    return (
      <div className="mb-md">
        <InlineErrorCard
          title="告警统计加载失败"
          message={state.error.message || '无法获取告警统计。'}
          onRetry={onRetry}
        />
      </div>
    )
  }

  if (!state.data) {
    return (
      <div className="mb-md">
        <InlineErrorCard
          title="告警统计为空"
          message="未获取到告警统计数据。"
          onRetry={onRetry}
        />
      </div>
    )
  }

  const stats = state.data

  return (
    <div className="mb-md grid grid-cols-2 lg:grid-cols-4 gap-sm">
      <AlertStatItem label="告警总量" value={formatInt(stats.total)} />
      <AlertStatItem label="未解决" value={formatInt(stats.open)} />
      <AlertStatItem label="已确认" value={formatInt(stats.acknowledged)} />
      <AlertStatItem label="已解决" value={formatInt(stats.resolved)} />
    </div>
  )
}

function AlertStatItem({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="flex flex-col gap-xs">
      <span className="text-caption">{label}</span>
      <span className="text-data-secondary" data-mono>
        {value}
      </span>
    </div>
  )
}

function formatInt(value: number): string {
  return Number.isFinite(value) ? Math.trunc(value).toLocaleString('zh-CN') : '0'
}
