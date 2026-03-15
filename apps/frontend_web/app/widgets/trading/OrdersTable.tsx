/**
 * OrdersTable — 订单列表
 *
 * 展示订单的标的、方向、数量、价格、状态，支持取消操作。
 */

import type { TradeOrder } from '@qp/api-client'
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
  Button,
} from '@qp/ui'

export interface OrdersTableProps {
  orders: TradeOrder[]
  loading?: boolean
  onCancel?: (orderId: string) => void
  cancelling?: string | null
}

const STATUS_LABEL: Record<string, string> = {
  pending: '待处理',
  filled: '已成交',
  cancelled: '已取消',
  failed: '失败',
}

const STATUS_CLASS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  filled: 'bg-green-100 text-green-800',
  cancelled: 'bg-secondary-200 text-secondary-600',
  failed: 'bg-red-100 text-red-800',
}

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function OrdersTable({
  orders,
  loading,
  onCancel,
  cancelling,
}: OrdersTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>标的</TableHeaderCell>
          <TableHeaderCell>方向</TableHeaderCell>
          <TableHeaderCell className="text-right">数量</TableHeaderCell>
          <TableHeaderCell className="text-right">价格</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell>时间</TableHeaderCell>
          {onCancel && <TableHeaderCell className="text-right">操作</TableHeaderCell>}
        </TableRow>
      </TableHead>
      <TableBody>
        {orders.length === 0 && !loading ? (
          <TableEmpty colSpan={onCancel ? 7 : 6} message="暂无订单" />
        ) : (
          orders.map((o) => (
            <TableRow key={o.id}>
              <TableCell>
                <span className="font-medium text-text-primary">
                  {o.symbol}
                </span>
              </TableCell>
              <TableCell>
                <span
                  className={
                    o.side === 'BUY' ? 'state-up font-medium' : 'state-down font-medium'
                  }
                >
                  {o.side === 'BUY' ? '买入' : '卖出'}
                </span>
              </TableCell>
              <TableCell className="text-right">
                <span className="text-data-mono">{o.quantity}</span>
              </TableCell>
              <TableCell className="text-right">
                <span className="text-data-mono">{fmt(o.price)}</span>
              </TableCell>
              <TableCell>
                <span
                  className={`inline-block px-sm py-xxs rounded-full text-caption ${STATUS_CLASS[o.status] ?? 'bg-secondary-100 text-secondary-600'}`}
                >
                  {STATUS_LABEL[o.status] ?? o.status}
                </span>
              </TableCell>
              <TableCell>
                <span className="text-caption text-text-muted">
                  {new Date(o.createdAt).toLocaleString('zh-CN')}
                </span>
              </TableCell>
              {onCancel && (
                <TableCell className="text-right">
                  {o.status === 'pending' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onCancel(o.id)}
                      loading={cancelling === o.id}
                    >
                      取消
                    </Button>
                  )}
                </TableCell>
              )}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}
