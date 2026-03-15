/**
 * AccountSummaryCards — 账户概览 KPI 卡片组
 *
 * 展示：现金余额 / 持仓市值 / 未实现盈亏 / 订单状态 / 成交统计
 */

import type { AccountOverview } from '@qp/api-client'
import { cn, transitionClass } from '@qp/ui'

export interface AccountSummaryCardsProps {
  overview: AccountOverview
}

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function pnlTone(n: number): string {
  if (n > 0) return 'state-up'
  if (n < 0) return 'state-down'
  return ''
}

export function AccountSummaryCards({ overview }: AccountSummaryCardsProps) {
  const cards: Array<{
    title: string
    value: string
    tone?: string
    sub?: string
  }> = [
    {
      title: '现金余额',
      value: `¥${fmt(overview.cashBalance)}`,
    },
    {
      title: '持仓市值',
      value: `¥${fmt(overview.totalMarketValue)}`,
      sub: `${overview.positionCount} 个持仓`,
    },
    {
      title: '未实现盈亏',
      value: `¥${fmt(overview.unrealizedPnl)}`,
      tone: pnlTone(overview.unrealizedPnl),
    },
    {
      title: '订单',
      value: `${overview.orderCount}`,
      sub: `待处理 ${overview.pendingOrderCount} · 已成交 ${overview.filledOrderCount}`,
    },
    {
      title: '成交统计',
      value: `${overview.tradeCount} 笔`,
      sub: `成交额 ¥${fmt(overview.turnover)}`,
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-md">
      {cards.map((card) => (
        <div
          key={card.title}
          className={cn(
            'bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md',
            transitionClass,
          )}
        >
          <p className="text-caption">{card.title}</p>
          <div
            className={cn('text-data-primary mt-sm', card.tone)}
            data-mono
          >
            {card.value}
          </div>
          {card.sub && (
            <p className="text-body-secondary mt-xs">{card.sub}</p>
          )}
        </div>
      ))}
    </div>
  )
}
