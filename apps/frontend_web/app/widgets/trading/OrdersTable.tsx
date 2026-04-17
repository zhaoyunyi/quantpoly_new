/**
 * OrdersTable — 订单列表
 *
 * 展示订单的标的、方向、数量、价格、状态，支持取消操作。
 */

import type { TradeOrder } from "@qp/api-client";
import { formatCurrency } from "../../shared/format";
import { exportCsv } from "../../shared/exportCsv";
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
  Button,
} from "@qp/ui";

export interface OrdersTableProps {
  orders: TradeOrder[];
  loading?: boolean;
  onCancel?: (orderId: string) => void;
  cancelling?: string | null;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "待处理",
  filled: "已成交",
  cancelled: "已取消",
  failed: "失败",
};

const STATUS_CLASS: Record<string, string> = {
  pending: "bg-state-warning-bg text-state-warning-text",
  filled: "bg-state-success-bg text-state-success-text",
  cancelled: "bg-secondary-200 text-secondary-600",
  failed: "bg-state-error-bg text-state-error-text",
};

export function OrdersTable({
  orders,
  loading,
  onCancel,
  cancelling,
}: OrdersTableProps) {
  const handleExport = () => {
    exportCsv(
      `orders-${new Date().toISOString().slice(0, 10)}.csv`,
      ['标的', '方向', '数量', '价格', '状态', '时间'],
      orders.map((o) => [
        o.symbol,
        o.side === 'BUY' ? '买入' : '卖出',
        String(o.quantity),
        String(o.price),
        STATUS_LABEL[o.status] ?? o.status,
        new Date(o.createdAt).toLocaleString('zh-CN'),
      ]),
    )
  }

  return (
    <div>
      {orders.length > 0 && (
        <div className="flex justify-end mb-sm">
          <Button variant="ghost" size="sm" onClick={handleExport}>
            导出 CSV
          </Button>
        </div>
      )}
      <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>标的</TableHeaderCell>
          <TableHeaderCell>方向</TableHeaderCell>
          <TableHeaderCell className="text-right">数量</TableHeaderCell>
          <TableHeaderCell className="text-right">价格</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell>时间</TableHeaderCell>
          {onCancel && (
            <TableHeaderCell className="text-right">操作</TableHeaderCell>
          )}
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
                    o.side === "BUY"
                      ? "state-up font-medium"
                      : "state-down font-medium"
                  }
                >
                  {o.side === "BUY" ? "买入" : "卖出"}
                </span>
              </TableCell>
              <TableCell className="text-right">
                <span className="text-data-mono">{o.quantity}</span>
              </TableCell>
              <TableCell className="text-right">
                <span className="text-data-mono">{formatCurrency(o.price)}</span>
              </TableCell>
              <TableCell>
                <span
                  className={`inline-block px-sm py-xxs rounded-full text-caption ${STATUS_CLASS[o.status] ?? "bg-secondary-100 text-secondary-600"}`}
                >
                  {STATUS_LABEL[o.status] ?? o.status}
                </span>
              </TableCell>
              <TableCell>
                <span className="text-caption text-text-muted">
                  {new Date(o.createdAt).toLocaleString("zh-CN")}
                </span>
              </TableCell>
              {onCancel && (
                <TableCell className="text-right">
                  {o.status === "pending" && (
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
    </div>
  );
}
