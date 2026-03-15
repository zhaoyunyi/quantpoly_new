/**
 * /trading/accounts — 账户管理页
 *
 * 功能：
 * - 账户列表（汇总概览）
 * - 创建新账户
 * - 编辑账户（名称/启停用）
 * - 查看过滤配置
 * - 资金操作（充值/提现）
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useCallback, useEffect, useState } from 'react'

import { ProtectedLayout } from '../../entry_wiring'
import {
  getTradingAccounts,
  getTradingAccountsAggregate,
  getAccountFilterConfig,
  createTradingAccount,
  updateTradingAccount,
  deposit,
  withdraw,
} from '@qp/api-client'
import type {
  TradingAccount,
  TradingAccountsAggregate,
  AccountFilterConfig,
  RangeStats,
  AppError,
} from '@qp/api-client'
import {
  Button,
  TextField,
  Dialog,
  Skeleton,
  EmptyState,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
  useToast,
} from '@qp/ui'

export const Route = createFileRoute('/trading/accounts')({
  component: TradingAccountsPage,
})

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function TradingAccountsPage() {
  const navigate = useNavigate()
  const toast = useToast()

  const [accounts, setAccounts] = useState<TradingAccount[]>([])
  const [aggregate, setAggregate] = useState<TradingAccountsAggregate | null>(null)
  const [filterConfig, setFilterConfig] = useState<AccountFilterConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /* 创建 */
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newCapital, setNewCapital] = useState('')
  const [creating, setCreating] = useState(false)

  /* 编辑 */
  const [editTarget, setEditTarget] = useState<TradingAccount | null>(null)
  const [editName, setEditName] = useState('')
  const [editing, setEditing] = useState(false)

  /* 充值/提现 */
  const [fundTarget, setFundTarget] = useState<TradingAccount | null>(null)
  const [fundAction, setFundAction] = useState<'deposit' | 'withdraw'>('deposit')
  const [fundAmount, setFundAmount] = useState('')
  const [funding, setFunding] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [accs, agg, fc] = await Promise.all([
        getTradingAccounts(),
        getTradingAccountsAggregate(),
        getAccountFilterConfig(),
      ])
      setAccounts(accs)
      setAggregate(agg)
      setFilterConfig(fc)
    } catch (err) {
      setError((err as AppError).message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  /* 创建账户 */
  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    try {
      const capital = parseFloat(newCapital)
      await createTradingAccount({
        accountName: newName.trim(),
        initialCapital: Number.isNaN(capital) ? undefined : capital,
      })
      toast.show('账户创建成功', 'success')
      setCreateOpen(false)
      setNewName('')
      setNewCapital('')
      void load()
    } catch (err) {
      toast.show((err as AppError).message || '创建失败', 'error')
    } finally {
      setCreating(false)
    }
  }

  /* 编辑账户 */
  const handleEdit = async () => {
    if (!editTarget) return
    setEditing(true)
    try {
      await updateTradingAccount(editTarget.id, {
        accountName: editName.trim() || undefined,
      })
      toast.show('账户已更新', 'success')
      setEditTarget(null)
      void load()
    } catch (err) {
      toast.show((err as AppError).message || '更新失败', 'error')
    } finally {
      setEditing(false)
    }
  }

  const handleToggleActive = async (account: TradingAccount) => {
    try {
      await updateTradingAccount(account.id, {
        isActive: !account.isActive,
      })
      toast.show(account.isActive ? '账户已停用' : '账户已启用', 'success')
      void load()
    } catch (err) {
      toast.show((err as AppError).message || '操作失败', 'error')
    }
  }

  /* 充值/提现 */
  const handleFund = async () => {
    if (!fundTarget) return
    const amount = parseFloat(fundAmount)
    if (Number.isNaN(amount) || amount <= 0) {
      toast.show('请输入有效金额', 'warning')
      return
    }
    setFunding(true)
    try {
      if (fundAction === 'deposit') {
        await deposit(fundTarget.id, amount)
        toast.show('充值成功', 'success')
      } else {
        await withdraw(fundTarget.id, amount)
        toast.show('提现成功', 'success')
      }
      setFundTarget(null)
      setFundAmount('')
      void load()
    } catch (err) {
      const appErr = err as AppError
      if (appErr.code === 'INSUFFICIENT_FUNDS') {
        toast.show('可用资金不足', 'error')
      } else {
        toast.show(appErr.message || '操作失败', 'error')
      }
    } finally {
      setFunding(false)
    }
  }

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题 */}
        <header className="flex items-start justify-between gap-md flex-wrap">
          <div className="flex-1 min-w-0">
            <button
              type="button"
              className="text-primary-500 hover:text-primary-700 text-body transition-all duration-[120ms] ease-out"
              onClick={() => void navigate({ to: '/trading' })}
            >
              ← 返回交易
            </button>
            <h1 className="text-title-page mt-xs">账户管理</h1>
            <p className="text-body-secondary mt-xs">
              创建和管理交易账户，执行充值与提现操作。
            </p>
          </div>
          <div className="shrink-0">
            <Button onClick={() => setCreateOpen(true)}>创建账户</Button>
          </div>
        </header>

        {/* 汇总卡片 */}
        {aggregate && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
            <SummaryCard title="账户总数" value={`${aggregate.accountCount}`} />
            <SummaryCard title="总权益" value={`¥${fmt(aggregate.totalEquity)}`} />
            <SummaryCard
              title="未实现盈亏"
              value={`¥${fmt(aggregate.totalUnrealizedPnl)}`}
              tone={aggregate.totalUnrealizedPnl}
            />
            <SummaryCard
              title="待处理订单"
              value={`${aggregate.pendingOrderCount}`}
            />
          </div>
        )}

        {/* 过滤配置 */}
        {filterConfig && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">过滤配置</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
              <SummaryCard title="账户数量" value={`${filterConfig.totalAccounts}`} />
              <SummaryCard
                title="有持仓账户"
                value={`${filterConfig.hasPositionsCount}`}
                sub={`无持仓 ${Math.max(0, filterConfig.totalAccounts - filterConfig.hasPositionsCount)}`}
              />
              <SummaryCard
                title="状态分布"
                value={`活跃 ${filterConfig.statusCounts.active ?? 0}`}
                sub={`停用 ${filterConfig.statusCounts.inactive ?? 0}`}
              />
              <SummaryCard
                title="风险等级"
                value={`低 ${filterConfig.riskLevelCounts.LOW ?? 0} · 中 ${filterConfig.riskLevelCounts.MEDIUM ?? 0}`}
                sub={`高 ${filterConfig.riskLevelCounts.HIGH ?? 0} · 未知 ${filterConfig.riskLevelCounts.UNKNOWN ?? 0}`}
              />
              <SummaryCard
                title="总资产（区间）"
                value={fmtRangeCurrency(filterConfig.totalAssets)}
                sub={fmtRangeAvgCurrency(filterConfig.totalAssets)}
              />
              <SummaryCard
                title="盈亏（区间）"
                value={fmtRangeCurrency(filterConfig.profitLoss)}
                sub={fmtRangeAvgCurrency(filterConfig.profitLoss)}
              />
              <SummaryCard
                title="盈亏率（区间）"
                value={fmtRangePercent(filterConfig.profitLossRate)}
                sub={fmtRangeAvgPercent(filterConfig.profitLossRate)}
              />
              <SummaryCard
                title="账户类型"
                value={Object.entries(filterConfig.accountTypeCounts)
                  .map(([k, v]) => `${k} ${v}`)
                  .join(' · ')}
              />
            </div>
          </section>
        )}

        {/* 账户列表 */}
        {loading ? (
          <div className="flex flex-col gap-sm">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} width="100%" height="48px" />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            title="加载失败"
            description={error}
            action={
              <Button variant="secondary" onClick={() => void load()}>
                重试
              </Button>
            }
          />
        ) : (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>账户名称</TableHeaderCell>
                  <TableHeaderCell>状态</TableHeaderCell>
                  <TableHeaderCell>创建时间</TableHeaderCell>
                  <TableHeaderCell className="text-right">操作</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accounts.length === 0 ? (
                  <TableEmpty colSpan={4} message="暂无账户" />
                ) : (
                  accounts.map((acc) => (
                    <TableRow key={acc.id}>
                      <TableCell>
                        <span className="font-medium text-text-primary">
                          {acc.accountName}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-block px-sm py-xxs rounded-full text-caption ${
                            acc.isActive
                              ? 'bg-green-100 text-green-800'
                              : 'bg-secondary-200 text-secondary-600'
                          }`}
                        >
                          {acc.isActive ? '活跃' : '停用'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-caption text-text-muted">
                          {new Date(acc.createdAt).toLocaleDateString('zh-CN')}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-xs">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditTarget(acc)
                              setEditName(acc.accountName)
                            }}
                          >
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void handleToggleActive(acc)}
                          >
                            {acc.isActive ? '停用' : '启用'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setFundTarget(acc)
                              setFundAction('deposit')
                              setFundAmount('')
                            }}
                          >
                            充值
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setFundTarget(acc)
                              setFundAction('withdraw')
                              setFundAmount('')
                            }}
                          >
                            提现
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </section>
        )}

        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>

      {/* 创建账户对话框 */}
      <Dialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="创建交易账户"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setCreateOpen(false)}
              disabled={creating}
            >
              取消
            </Button>
            <Button
              loading={creating}
              onClick={() => void handleCreate()}
              disabled={!newName.trim()}
            >
              创建
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-md">
          <TextField
            label="账户名称"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="我的交易账户"
          />
          <TextField
            label="初始资金（可选）"
            type="number"
            value={newCapital}
            onChange={(e) => setNewCapital(e.target.value)}
            placeholder="100000"
            help="不填则默认 0"
          />
        </div>
      </Dialog>

      {/* 编辑账户对话框 */}
      <Dialog
        open={!!editTarget}
        onOpenChange={(open) => {
          if (!open) setEditTarget(null)
        }}
        title="编辑账户"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setEditTarget(null)}
              disabled={editing}
            >
              取消
            </Button>
            <Button loading={editing} onClick={() => void handleEdit()}>
              保存
            </Button>
          </>
        }
      >
        <TextField
          label="账户名称"
          value={editName}
          onChange={(e) => setEditName(e.target.value)}
        />
      </Dialog>

      {/* 充值/提现对话框 */}
      <Dialog
        open={!!fundTarget}
        onOpenChange={(open) => {
          if (!open) setFundTarget(null)
        }}
        title={fundAction === 'deposit' ? '充值' : '提现'}
        description={`对账户「${fundTarget?.accountName ?? ''}」进行${fundAction === 'deposit' ? '充值' : '提现'}操作。`}
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setFundTarget(null)}
              disabled={funding}
            >
              取消
            </Button>
            <Button loading={funding} onClick={() => void handleFund()}>
              确认
            </Button>
          </>
        }
      >
        <TextField
          label="金额"
          type="number"
          value={fundAmount}
          onChange={(e) => setFundAmount(e.target.value)}
          placeholder="0.00"
        />
      </Dialog>
    </ProtectedLayout>
  )
}

function SummaryCard({
  title,
  value,
  tone,
  sub,
}: {
  title: string
  value: string
  tone?: number
  sub?: string
}) {
  const toneClass =
    tone !== undefined
      ? tone > 0
        ? 'state-up'
        : tone < 0
          ? 'state-down'
          : ''
      : ''
  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
      <p className="text-caption">{title}</p>
      <div className={`text-data-primary mt-sm ${toneClass}`} data-mono>
        {value}
      </div>
      {sub ? <p className="text-body-secondary mt-xs">{sub}</p> : null}
    </div>
  )
}

function fmtRangeCurrency(value: RangeStats | null): string {
  if (!value) return '—'
  return `¥${fmt(value.min)} ~ ¥${fmt(value.max)}`
}

function fmtRangeAvgCurrency(value: RangeStats | null): string | undefined {
  if (!value) return undefined
  return `均值 ¥${fmt(value.average)}`
}

function fmtRangePercent(value: RangeStats | null): string {
  if (!value) return '—'
  return `${(value.min * 100).toFixed(1)}% ~ ${(value.max * 100).toFixed(1)}%`
}

function fmtRangeAvgPercent(value: RangeStats | null): string | undefined {
  if (!value) return undefined
  return `均值 ${(value.average * 100).toFixed(1)}%`
}
