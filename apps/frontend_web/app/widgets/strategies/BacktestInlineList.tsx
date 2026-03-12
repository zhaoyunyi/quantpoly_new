/**
 * 回测内嵌列表组件
 *
 * 在策略详情页中内嵌展示关联的回测列表。
 * 支持加载态、空状态与快捷创建回测。
 */

import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
  Skeleton,
  Button,
} from "@qp/ui";
import type { StrategyBacktest } from "@qp/api-client";

export interface BacktestInlineListProps {
  items: StrategyBacktest[];
  loading?: boolean;
  onCreateBacktest?: () => void;
}

const statusLabels: Record<string, string> = {
  pending: "排队中",
  running: "运行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

export function BacktestInlineList({
  items,
  loading,
  onCreateBacktest,
}: BacktestInlineListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-sm">
        {Array.from({ length: 3 }).map((_, idx) => (
          <Skeleton key={idx} width="100%" height="36px" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-title-card">关联回测</h3>
        {onCreateBacktest && (
          <Button variant="secondary" size="sm" onClick={onCreateBacktest}>
            快捷创建回测
          </Button>
        )}
      </div>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>回测 ID</TableHeaderCell>
            <TableHeaderCell>状态</TableHeaderCell>
            <TableHeaderCell>创建时间</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.length === 0 ? (
            <TableEmpty colSpan={3} message="暂无关联回测数据。" />
          ) : (
            items.map((bt) => (
              <TableRow key={bt.id}>
                <TableCell>
                  <span className="text-data-mono text-caption">
                    {bt.id.length > 12 ? `${bt.id.slice(0, 12)}…` : bt.id}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-caption">
                    {statusLabels[bt.status] ?? bt.status}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-data-mono">
                    {formatDate(bt.createdAt)}
                  </span>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function formatDate(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
  }
}
