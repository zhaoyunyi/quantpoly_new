/**
 * EquityCurveChart — 权益曲线图（占位实现）
 *
 * 以纯 CSS 简易柱状图展示曲线走势；
 * 后续可替换为 Recharts / Visx 等图表库。
 */

import type { EquityCurvePoint } from '@qp/api-client'
import { cn, transitionClass } from '@qp/ui'

export interface EquityCurveChartProps {
  data: EquityCurvePoint[]
}

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function EquityCurveChart({ data }: EquityCurveChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg text-center">
        <p className="text-body-secondary">暂无权益数据</p>
      </div>
    )
  }

  const equities = data.map((d) => d.equity)
  const maxEquity = Math.max(...equities)
  const minEquity = Math.min(...equities)
  const range = maxEquity - minEquity || 1
  const lastPoint = data[data.length - 1]

  return (
    <div
      className={cn(
        'bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg',
        transitionClass,
      )}
    >
      <div className="flex items-start justify-between mb-md">
        <h3 className="text-title-card">权益曲线</h3>
        <div className="text-right">
          <div className="text-data-primary" data-mono>
            ¥{fmt(lastPoint.equity)}
          </div>
          <div className="text-caption text-text-muted">
            最新权益
          </div>
        </div>
      </div>

      {/* 简易柱状图 */}
      <div className="flex items-end gap-px h-32">
        {data.map((point, idx) => {
          const height =
            ((point.equity - minEquity) / range) * 100
          const isLast = idx === data.length - 1
          return (
            <div
              key={point.timestamp}
              className={cn(
                'flex-1 rounded-t-sm transition-all duration-[120ms] ease-out min-w-[2px]',
                isLast ? 'bg-primary-500' : 'bg-primary-300/60',
              )}
              style={{ height: `${Math.max(height, 2)}%` }}
              title={`${new Date(point.timestamp).toLocaleDateString('zh-CN')} — ¥${fmt(point.equity)}`}
            />
          )
        })}
      </div>

      {/* 时间轴标注 */}
      <div className="flex justify-between mt-xs">
        <span className="text-caption text-text-muted">
          {new Date(data[0].timestamp).toLocaleDateString('zh-CN')}
        </span>
        <span className="text-caption text-text-muted">
          {new Date(lastPoint.timestamp).toLocaleDateString('zh-CN')}
        </span>
      </div>
    </div>
  )
}
