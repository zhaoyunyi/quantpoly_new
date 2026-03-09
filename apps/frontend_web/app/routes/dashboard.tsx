import { createFileRoute } from '@tanstack/react-router'

import { ProtectedLayout } from '../entry_wiring'
import {
  getBacktestStatistics,
  getMonitorSummary,
  getRiskAlertStats,
  getSignalsDashboard,
  getTradingAccountsAggregate,
} from '@qp/api-client'
import type {
  BacktestStatistics,
  MonitorSummary,
  RiskAlertStats,
  SignalsDashboard,
  TradingAccountsAggregate,
  AppError,
} from '@qp/api-client'
import { Skeleton } from '@qp/ui'
import { useLoadable } from '../shared/useLoadable'
import { DegradedBanner } from '../widgets/dashboard/DegradedBanner'
import { InlineErrorCard } from '../widgets/dashboard/InlineErrorCard'
import { KpiCard, type KpiTone } from '../widgets/dashboard/KpiCard'
import { Panel } from '../widgets/dashboard/Panel'
import { QuickActions } from '../widgets/dashboard/QuickActions'
import { StatusPill } from '../widgets/dashboard/StatusPill'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})

export function DashboardPage() {
  const summary = useLoadable<MonitorSummary>(getMonitorSummary)
  const aggregate = useLoadable<TradingAccountsAggregate>(getTradingAccountsAggregate)
  const backtestStats = useLoadable<BacktestStatistics>(getBacktestStatistics)
  const riskAlertStats = useLoadable<RiskAlertStats>(getRiskAlertStats)
  const signalsDashboard = useLoadable<SignalsDashboard>(getSignalsDashboard)

  const degradedEnabled = !!summary.data?.degraded?.enabled
  const degradedReasons = summary.data?.degraded?.reasons ?? []

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <h1 className="text-title-page">仪表盘</h1>
            <p className="text-body-secondary mt-xs">
              登录后的总览入口，聚合账户/策略/回测/任务/信号/告警的关键状态。
            </p>
          </div>
          <div className="shrink-0">
            {summary.loading ? (
              <Skeleton width="84px" height="28px" />
            ) : degradedEnabled ? (
              <StatusPill variant="degraded" label="DEGRADED" />
            ) : (
              <StatusPill variant="ok" label="OK" />
            )}
          </div>
        </header>

        {degradedEnabled && <DegradedBanner reasons={degradedReasons} />}

        {/* 快速入口 */}
        <QuickActions />

        {/* KPI Cards（结论优先） */}
        <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-md">
          <SummaryKpis
            state={summary}
            onRetry={() => void summary.reload()}
          />
        </section>

        {/* 次级统计面板 */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-md">
          <Panel title="资产概览" subtitle="来自交易账户聚合统计（/trading/accounts/aggregate）">
            <AggregatePanel state={aggregate} onRetry={() => void aggregate.reload()} />
          </Panel>
          <Panel title="回测统计" subtitle="来自回测统计（/backtests/statistics）">
            <BacktestPanel state={backtestStats} onRetry={() => void backtestStats.reload()} />
          </Panel>
          <Panel title="告警统计" subtitle="来自风控告警统计（/risk/alerts/stats）">
            <RiskAlertStatsPanel
              state={riskAlertStats}
              onRetry={() => void riskAlertStats.reload()}
            />
          </Panel>
          <Panel title="信号统计" subtitle="来自信号面板（/signals/dashboard）">
            <SignalsDashboardPanel
              state={signalsDashboard}
              onRetry={() => void signalsDashboard.reload()}
            />
          </Panel>
        </section>
      </div>
    </ProtectedLayout>
  )
}

function SummaryKpis({
  state,
  onRetry,
}: {
  state: {
    loading: boolean
    data: MonitorSummary | null
    error: AppError | null
  }
  onRetry: () => void
}) {
  if (state.loading) {
    return (
      <>
        {Array.from({ length: 6 }).map((_, idx) => (
          <div
            key={idx}
            className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md"
          >
            <Skeleton width="40%" height="12px" />
            <div className="mt-sm flex items-baseline justify-between gap-md">
              <Skeleton width="40%" height="26px" />
              <Skeleton width="28%" height="18px" />
            </div>
          </div>
        ))}
      </>
    )
  }

  if (state.error) {
    return (
      <InlineErrorCard
        title="运营摘要加载失败"
        message={state.error.message || '无法获取监控摘要，请稍后重试。'}
        onRetry={onRetry}
        className="xl:col-span-3"
      />
    )
  }

  const s = state.data
  if (!s) {
    return (
      <InlineErrorCard
        title="运营摘要为空"
        message="未获取到摘要数据。"
        onRetry={onRetry}
        className="xl:col-span-3"
      />
    )
  }

  return (
    <>
      <KpiCard
        title="账户"
        value={formatInt(s.accounts.total)}
        subvalue={`活跃 ${formatInt(s.accounts.active)}`}
        href="/accounts"
      />
      <KpiCard
        title="策略"
        value={formatInt(s.strategies.total)}
        subvalue={`活跃 ${formatInt(s.strategies.active)}`}
        href="/strategies"
      />
      <KpiCard
        title="回测"
        value={formatInt(s.backtests.total)}
        subvalue={`运行 ${formatInt(s.backtests.running)}`}
        href="/backtests"
      />
      <KpiCard
        title="任务"
        value={formatInt(s.tasks.total)}
        subvalue={`运行 ${formatInt(s.tasks.running)} / 失败 ${formatInt(s.tasks.failed)}`}
        tone={s.tasks.failed > 0 ? 'risk' : 'default'}
      />
      <KpiCard
        title="信号"
        value={formatInt(s.signals.total)}
        subvalue={`待处理 ${formatInt(s.signals.pending)}`}
        href="/monitor"
      />
      <KpiCard
        title="告警"
        value={formatInt(s.alerts.open)}
        subvalue={`严重 ${formatInt(s.alerts.critical)}`}
        tone={s.alerts.critical > 0 ? 'risk' : 'default'}
        href="/monitor"
      />
    </>
  )
}

function AggregatePanel({
  state,
  onRetry,
}: {
  state: {
    loading: boolean
    data: TradingAccountsAggregate | null
    error: AppError | null
  }
  onRetry: () => void
}) {
  if (state.loading) {
    return (
      <div className="grid grid-cols-2 gap-md">
        {Array.from({ length: 6 }).map((_, idx) => (
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
      <InlineErrorCard
        title="资产聚合加载失败"
        message={state.error.message || '无法获取资产概览。'}
        onRetry={onRetry}
      />
    )
  }

  const a = state.data
  if (!a) {
    return (
      <InlineErrorCard
        title="资产聚合为空"
        message="未获取到资产聚合数据。"
        onRetry={onRetry}
      />
    )
  }

  const pnlTone: KpiTone = a.totalUnrealizedPnl > 0 ? 'up' : a.totalUnrealizedPnl < 0 ? 'down' : 'default'

  return (
    <div className="grid grid-cols-2 gap-md">
      <Metric label="账户数" value={formatInt(a.accountCount)} />
      <Metric label="待处理订单" value={formatInt(a.pendingOrderCount)} tone={a.pendingOrderCount > 0 ? 'risk' : 'default'} />
      <Metric label="总权益" value={formatNumber(a.totalEquity)} />
      <Metric label="现金余额" value={formatNumber(a.totalCashBalance)} />
      <Metric label="持仓市值" value={formatNumber(a.totalMarketValue)} />
      <Metric label="未实现盈亏" value={formatNumber(a.totalUnrealizedPnl)} tone={pnlTone} />
    </div>
  )
}

function BacktestPanel({
  state,
  onRetry,
}: {
  state: {
    loading: boolean
    data: BacktestStatistics | null
    error: AppError | null
  }
  onRetry: () => void
}) {
  if (state.loading) {
    return (
      <div className="grid grid-cols-2 gap-md">
        {Array.from({ length: 6 }).map((_, idx) => (
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
      <InlineErrorCard
        title="回测统计加载失败"
        message={state.error.message || '无法获取回测统计。'}
        onRetry={onRetry}
      />
    )
  }

  const s = state.data
  if (!s) {
    return (
      <InlineErrorCard
        title="回测统计为空"
        message="未获取到回测统计数据。"
        onRetry={onRetry}
      />
    )
  }

  return (
    <div className="grid grid-cols-2 gap-md">
      <Metric label="总回测" value={formatInt(s.totalCount)} />
      <Metric label="已完成" value={formatInt(s.completedCount)} />
      <Metric label="运行中" value={formatInt(s.runningCount)} />
      <Metric label="失败" value={formatInt(s.failedCount)} tone={s.failedCount > 0 ? 'risk' : 'default'} />
      <Metric label="平均收益率" value={formatPercent(s.averageReturnRate)} />
      <Metric label="平均最大回撤" value={formatPercent(s.averageMaxDrawdown)} tone={s.averageMaxDrawdown > 0.2 ? 'risk' : 'default'} />
    </div>
  )
}

function RiskAlertStatsPanel({
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
      <div className="grid grid-cols-2 gap-md">
        {Array.from({ length: 6 }).map((_, idx) => (
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
      <InlineErrorCard
        title="告警统计加载失败"
        message={state.error.message || '无法获取告警统计。'}
        onRetry={onRetry}
      />
    )
  }

  const s = state.data
  if (!s) {
    return (
      <InlineErrorCard
        title="告警统计为空"
        message="未获取到告警统计数据。"
        onRetry={onRetry}
      />
    )
  }

  return (
    <div className="grid grid-cols-2 gap-md">
      <Metric label="总告警" value={formatInt(s.total)} />
      <Metric label="未解决" value={formatInt(s.open)} tone={s.open > 0 ? 'risk' : 'default'} />
      <Metric label="已确认" value={formatInt(s.acknowledged)} />
      <Metric label="已解决" value={formatInt(s.resolved)} />
      <Metric label="严重" value={formatInt(s.bySeverity?.critical ?? 0)} tone={(s.bySeverity?.critical ?? 0) > 0 ? 'risk' : 'default'} />
      <Metric label="高风险" value={formatInt(s.bySeverity?.high ?? 0)} tone={(s.bySeverity?.high ?? 0) > 0 ? 'risk' : 'default'} />
    </div>
  )
}

function SignalsDashboardPanel({
  state,
  onRetry,
}: {
  state: {
    loading: boolean
    data: SignalsDashboard | null
    error: AppError | null
  }
  onRetry: () => void
}) {
  if (state.loading) {
    return (
      <div className="grid grid-cols-2 gap-md">
        {Array.from({ length: 6 }).map((_, idx) => (
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
      <InlineErrorCard
        title="信号统计加载失败"
        message={state.error.message || '无法获取信号统计。'}
        onRetry={onRetry}
      />
    )
  }

  const s = state.data
  if (!s) {
    return (
      <InlineErrorCard
        title="信号统计为空"
        message="未获取到信号统计数据。"
        onRetry={onRetry}
      />
    )
  }

  return (
    <div className="grid grid-cols-2 gap-md">
      <Metric label="总信号" value={formatInt(s.total)} />
      <Metric label="待处理" value={formatInt(s.pending)} tone={s.pending > 0 ? 'risk' : 'default'} />
      <Metric label="已执行" value={formatInt(s.executed)} tone={s.executed > 0 ? 'up' : 'default'} />
      <Metric label="已取消" value={formatInt(s.cancelled)} />
      <Metric label="已过期" value={formatInt(s.expired)} tone={s.expired > 0 ? 'down' : 'default'} />
      <Metric label="分账户" value={formatInt(s.byAccount?.length ?? 0)} />
    </div>
  )
}

function Metric({
  label,
  value,
  tone = 'default',
}: {
  label: string
  value: string
  tone?: KpiTone
}) {
  const valueClass =
    tone === 'up'
      ? 'text-data-secondary state-up'
      : tone === 'down'
        ? 'text-data-secondary state-down'
        : tone === 'risk'
          ? 'text-data-secondary state-risk'
          : 'text-data-secondary'

  return (
    <div className="flex flex-col gap-xs">
      <span className="text-caption">{label}</span>
      <span className={valueClass} data-mono>
        {value}
      </span>
    </div>
  )
}

function formatInt(value: number): string {
  return Number.isFinite(value) ? Math.trunc(value).toLocaleString('zh-CN') : '0'
}

function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return '0.00'
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return '0.00%'
  return `${(value * 100).toFixed(2)}%`
}
