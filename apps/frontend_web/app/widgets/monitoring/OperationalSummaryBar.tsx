import type { MonitorSummary } from '@qp/api-client'

export function OperationalSummaryBar({ summary }: { summary: MonitorSummary }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
      <SummaryItem label="任务运行中" value={formatInt(summary.tasks.running)} />
      <SummaryItem label="信号待处理" value={formatInt(summary.signals.pending)} />
      <SummaryItem label="告警未解决" value={formatInt(summary.alerts.open)} />
      <SummaryItem label="严重告警" value={formatInt(summary.alerts.critical)} />
    </div>
  )
}

function SummaryItem({ label, value }: { label: string; value: string }) {
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

