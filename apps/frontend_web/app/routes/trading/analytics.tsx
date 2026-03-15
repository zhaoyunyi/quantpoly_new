/**
 * /trading/analytics — 分析报表页
 *
 * 功能：
 * - 风险指标
 * - 权益曲线
 * - 交易统计
 * - 资金流水
 * - 风险评估（含 202 PENDING 处理）
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useCallback, useState } from 'react'

import { ProtectedLayout } from '../../entry_wiring'
import {
  getRiskMetrics,
  getEquityCurve,
  getTradeStats,
  getCashFlows,
  getCashFlowSummary,
  getRiskAssessment,
  evaluateRiskAssessment,
} from '@qp/api-client'
import type {
  RiskMetrics,
  EquityCurvePoint,
  TradeStats,
  CashFlow,
  CashFlowSummary,
  RiskAssessment,
  AppError,
} from '@qp/api-client'
import { Button, Skeleton, EmptyState, useToast } from '@qp/ui'
import { AccountSelector } from '../../widgets/trading/AccountSelector'
import { CashFlowTable } from '../../widgets/trading/CashFlowTable'
import { EquityCurveChart } from '../../widgets/trading/EquityCurveChart'

export const Route = createFileRoute('/trading/analytics')({
  component: TradingAnalyticsPage,
})

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const RISK_LEVEL_LABEL: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
}

const RISK_LEVEL_CLASS: Record<string, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-red-100 text-red-800',
}

export function TradingAnalyticsPage() {
  const navigate = useNavigate()
  const toast = useToast()

  const [accountId, setAccountId] = useState('')
  const [loading, setLoading] = useState(false)

  /* data */
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null)
  const [equityCurve, setEquityCurve] = useState<EquityCurvePoint[]>([])
  const [tradeStats, setTradeStats] = useState<TradeStats | null>(null)
  const [cashFlows, setCashFlows] = useState<CashFlow[]>([])
  const [cashFlowSummary, setCashFlowSummary] = useState<CashFlowSummary | null>(null)
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null)
  const [riskPending, setRiskPending] = useState(false)
  const [evaluating, setEvaluating] = useState(false)

  const loadAll = useCallback(
    async (id: string) => {
      if (!id) return
      setLoading(true)
      setRiskPending(false)
      try {
        const [rm, ec, ts, cf, cfs] = await Promise.all([
          getRiskMetrics(id).catch(() => null),
          getEquityCurve(id).catch(() => []),
          getTradeStats(id).catch(() => null),
          getCashFlows(id).catch(() => []),
          getCashFlowSummary(id).catch(() => null),
        ])
        setRiskMetrics(rm)
        setEquityCurve(ec)
        setTradeStats(ts)
        setCashFlows(cf)
        setCashFlowSummary(cfs)

        // 风险评估单独处理 202
        try {
          const ra = await getRiskAssessment(id)
          setRiskAssessment(ra)
        } catch (err) {
          const appErr = err as AppError
          if (appErr.code === 'RISK_ASSESSMENT_PENDING') {
            setRiskPending(true)
          }
          // 其它错误静默
        }
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const handleSelectAccount = (id: string) => {
    setAccountId(id)
    void loadAll(id)
  }

  const handleEvaluate = async () => {
    if (!accountId) return
    setEvaluating(true)
    try {
      const ra = await evaluateRiskAssessment(accountId)
      setRiskAssessment(ra)
      setRiskPending(false)
      toast.show('风险评估完成', 'success')
    } catch (err) {
      const appErr = err as AppError
      if (appErr.code === 'RISK_ASSESSMENT_PENDING') {
        setRiskPending(true)
        toast.show('风险评估正在生成中，请稍后刷新', 'info')
      } else {
        toast.show(appErr.message || '评估失败', 'error')
      }
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题 */}
        <header>
          <button
            type="button"
            className="text-primary-500 hover:text-primary-700 text-body transition-all duration-[120ms] ease-out"
            onClick={() => void navigate({ to: '/trading' })}
          >
            ← 返回交易
          </button>
          <h1 className="text-title-page mt-xs">分析报表</h1>
          <p className="text-body-secondary mt-xs">
            查看账户风险指标、权益曲线、交易统计与资金流水。
          </p>
        </header>

        {/* 账户选择 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <AccountSelector
            value={accountId}
            onValueChange={handleSelectAccount}
            className="w-64"
          />
        </section>

        {!accountId ? (
          <EmptyState
            title="请选择交易账户"
            description="选择账户以查看分析报表。"
          />
        ) : loading ? (
          <div className="flex flex-col gap-md">
            <Skeleton width="100%" height="160px" />
            <Skeleton width="100%" height="200px" />
          </div>
        ) : (
          <>
            {/* 风险指标 */}
            {riskMetrics && (
              <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
                <h2 className="text-title-section mb-md">风险指标</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
                  <MetricItem label="风险评分" value={`${riskMetrics.riskScore}`} />
                  <MetricItem
                    label="风险等级"
                    value={RISK_LEVEL_LABEL[riskMetrics.riskLevel] ?? riskMetrics.riskLevel}
                    badge={RISK_LEVEL_CLASS[riskMetrics.riskLevel]}
                  />
                  <MetricItem
                    label="敞口比率"
                    value={`${(riskMetrics.exposureRatio * 100).toFixed(1)}%`}
                  />
                  <MetricItem label="杠杆" value={`${riskMetrics.leverage.toFixed(2)}x`} />
                </div>
              </section>
            )}

            {/* 权益曲线 */}
            <EquityCurveChart data={equityCurve} />

            {/* 交易统计 */}
            {tradeStats && (
              <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
                <h2 className="text-title-section mb-md">交易统计</h2>
                <div className="grid grid-cols-2 gap-md">
                  <MetricItem label="成交笔数" value={`${tradeStats.tradeCount}`} />
                  <MetricItem label="成交额" value={`¥${fmt(tradeStats.turnover)}`} />
                </div>
              </section>
            )}

            {/* 资金流水 */}
            <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
              <div className="flex items-center justify-between mb-md">
                <h2 className="text-title-section">资金流水</h2>
                {cashFlowSummary && (
                  <div className="flex gap-lg text-caption text-text-secondary">
                    <span>流入 ¥{fmt(cashFlowSummary.totalInflow)}</span>
                    <span>流出 ¥{fmt(Math.abs(cashFlowSummary.totalOutflow))}</span>
                    <span
                      className={
                        cashFlowSummary.netFlow >= 0 ? 'state-up' : 'state-down'
                      }
                    >
                      净流 ¥{fmt(cashFlowSummary.netFlow)}
                    </span>
                  </div>
                )}
              </div>
              <CashFlowTable flows={cashFlows} />
            </section>

            {/* 风险评估 */}
            <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
              <div className="flex items-center justify-between mb-md">
                <h2 className="text-title-section">风险评估</h2>
                <Button
                  variant="secondary"
                  size="sm"
                  loading={evaluating}
                  onClick={() => void handleEvaluate()}
                >
                  发起评估
                </Button>
              </div>

              {riskPending ? (
                <div
                  className="flex items-center gap-sm p-md rounded-md bg-yellow-50 border border-yellow-200"
                  role="alert"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                    className="text-yellow-600 shrink-0"
                  >
                    <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
                    <path
                      d="M8 5v3.5M8 10.5v.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="text-body text-yellow-800">
                    风险评估快照正在生成中，请稍后刷新查看结果。
                  </span>
                </div>
              ) : riskAssessment ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
                  <MetricItem
                    label="评估 ID"
                    value={riskAssessment.assessmentId.slice(0, 8)}
                  />
                  <MetricItem
                    label="风险评分"
                    value={`${riskAssessment.riskScore}`}
                  />
                  <MetricItem
                    label="风险等级"
                    value={RISK_LEVEL_LABEL[riskAssessment.riskLevel] ?? riskAssessment.riskLevel}
                    badge={RISK_LEVEL_CLASS[riskAssessment.riskLevel]}
                  />
                  <MetricItem
                    label="触发规则"
                    value={
                      riskAssessment.triggeredRuleIds.length > 0
                        ? riskAssessment.triggeredRuleIds.join(', ')
                        : '无'
                    }
                  />
                </div>
              ) : (
                <p className="text-body-secondary">暂无评估数据，点击"发起评估"开始。</p>
              )}
            </section>
          </>
        )}

        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  )
}

function MetricItem({
  label,
  value,
  badge,
}: {
  label: string
  value: string
  badge?: string
}) {
  return (
    <div>
      <p className="text-caption text-text-secondary">{label}</p>
      {badge ? (
        <span
          className={`inline-block px-sm py-xxs rounded-full text-caption mt-xs ${badge}`}
        >
          {value}
        </span>
      ) : (
        <p className="text-data-primary mt-xs" data-mono>
          {value}
        </p>
      )}
    </div>
  )
}
