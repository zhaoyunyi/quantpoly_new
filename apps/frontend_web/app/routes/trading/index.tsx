/**
 * /trading — 交易主控页
 *
 * 功能：
 * - 账户选择
 * - 账户概览 KPI 卡片
 * - 持仓列表
 * - 订单列表（带取消）
 * - 快捷买入/卖出下单
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useCallback, useState } from 'react'

import { ProtectedLayout } from '../../entry_wiring'
import {
  getAccountOverview,
  getPositions,
  getOrders,
  cancelOrder,
} from '@qp/api-client'
import type {
  AccountOverview,
  Position,
  TradeOrder,
  AppError,
} from '@qp/api-client'
import { Button, Skeleton, EmptyState, useToast } from '@qp/ui'
import { usePolling } from '../../shared/usePolling'
import { LastUpdated } from '../../shared/LastUpdated'
import { AccountSelector } from '../../widgets/trading/AccountSelector'
import { AccountSummaryCards } from '../../widgets/trading/AccountSummaryCards'
import { PositionsTable } from '../../widgets/trading/PositionsTable'
import { OrdersTable } from '../../widgets/trading/OrdersTable'
import { OrderTicket } from '../../widgets/trading/OrderTicket'

export const Route = createFileRoute('/trading/')({
  component: TradingPage,
})

export function TradingPage() {
  const navigate = useNavigate()
  const toast = useToast()

  const [accountId, setAccountId] = useState('')
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null)

  const loadAccountData = useCallback(async () => {
    const [ov, pos, ord] = await Promise.all([
      getAccountOverview(accountId),
      getPositions(accountId),
      getOrders(accountId),
    ])
    return { overview: ov, positions: pos, orders: ord }
  }, [accountId])

  const accountData = usePolling<{
    overview: AccountOverview
    positions: Position[]
    orders: TradeOrder[]
  }>(loadAccountData, 15_000, !!accountId)

  const overview = accountData.data?.overview ?? null
  const positions = accountData.data?.positions ?? []
  const orders = accountData.data?.orders ?? []
  const loading = accountData.loading
  const error = accountData.error

  const handleSelectAccount = (id: string) => {
    setAccountId(id)
  }

  const handleCancelOrder = async (orderId: string) => {
    if (!accountId) return
    setCancellingOrder(orderId)
    try {
      await cancelOrder(accountId, orderId)
      toast.show('订单已取消', 'success')
      void accountData.reload()
    } catch (err) {
      toast.show((err as AppError).message || '取消失败', 'error')
    } finally {
      setCancellingOrder(null)
    }
  }

  const handleOrderSuccess = () => {
    void accountData.reload()
  }

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题 */}
        <header className="flex items-start justify-between gap-md flex-wrap">
          <div className="flex-1 min-w-0">
            <h1 className="text-title-page">交易</h1>
            <p className="text-body-secondary mt-xs">
              选择账户进行交易操作，查看持仓和订单状态。
            </p>
          </div>
          <div className="shrink-0 flex gap-sm">
            <Button
              variant="secondary"
              onClick={() => void navigate({ to: '/trading/accounts' })}
            >
              账户管理
            </Button>
            <Button
              variant="secondary"
              onClick={() => void navigate({ to: '/trading/analytics' })}
            >
              分析报表
            </Button>
          </div>
        </header>

        {/* 账户选择 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <AccountSelector
            value={accountId}
            onValueChange={handleSelectAccount}
            className="w-64"
          />
        </section>

        {/* 数据展示 */}
        {!accountId ? (
          <EmptyState
            title="请选择交易账户"
            description="从上方下拉菜单选择一个账户以查看交易数据。"
            variant="first-use"
          />
        ) : loading && !overview ? (
          <div className="flex flex-col gap-md">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-md">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} width="100%" height="80px" />
              ))}
            </div>
            <Skeleton width="100%" height="200px" />
          </div>
        ) : accountData.error ? (
          <EmptyState
            title="加载失败"
            description={accountData.error.message || '加载账户数据失败'}
            variant="error"
            action={
              <Button
                variant="secondary"
                onClick={() => void accountData.reload()}
              >
                重试
              </Button>
            }
          />
        ) : (
          overview && (
            <>
              {/* 概览卡片 */}
              <AccountSummaryCards overview={overview} />

              <div className="flex items-center justify-between">
                <p className="text-caption text-text-muted">
                  持仓价格来自最近成交，可能存在延迟
                </p>
                <LastUpdated
                  lastUpdatedAt={accountData.lastUpdatedAt}
                  onRefresh={() => void accountData.reload()}
                  loading={loading}
                />
              </div>

              {/* 主体：持仓 + 下单 */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg">
                {/* 持仓表 + 订单表 */}
                <div className="lg:col-span-2 flex flex-col gap-lg">
                  <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
                    <h2 className="text-title-section mb-md">持仓</h2>
                    <PositionsTable positions={positions} loading={loading} />
                  </section>

                  <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
                    <h2 className="text-title-section mb-md">订单</h2>
                    <OrdersTable
                      orders={orders}
                      loading={loading}
                      onCancel={(oid) => void handleCancelOrder(oid)}
                      cancelling={cancellingOrder}
                    />
                  </section>
                </div>

                {/* 右侧下单面板 */}
                <div>
                  <OrderTicket
                    accountId={accountId}
                    onSuccess={handleOrderSuccess}
                  />
                </div>
              </div>
            </>
          )
        )}

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  )
}
