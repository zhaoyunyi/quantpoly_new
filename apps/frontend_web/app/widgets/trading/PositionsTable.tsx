/**
 * PositionsTable — 持仓列表
 *
 * 展示当前持仓的标的、数量、成本价、现价、市值、盈亏。
 */

import type { Position } from "@qp/api-client";
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
} from "@qp/ui";

export interface PositionsTableProps {
  positions: Position[];
  loading?: boolean;
}

function fmt(n: number): string {
  return n.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function PositionsTable({ positions, loading }: PositionsTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>标的</TableHeaderCell>
          <TableHeaderCell className="text-right">数量</TableHeaderCell>
          <TableHeaderCell className="text-right">成本价</TableHeaderCell>
          <TableHeaderCell className="text-right">现价</TableHeaderCell>
          <TableHeaderCell className="text-right">市值</TableHeaderCell>
          <TableHeaderCell className="text-right">未实现盈亏</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {positions.length === 0 && !loading ? (
          <TableEmpty colSpan={6} message="暂无持仓" />
        ) : (
          positions.map((p) => {
            const marketValue = p.quantity * p.lastPrice;
            const costValue = p.quantity * p.avgPrice;
            const pnl = marketValue - costValue;
            const pnlClass = pnl > 0 ? "state-up" : pnl < 0 ? "state-down" : "";

            return (
              <TableRow key={p.id}>
                <TableCell>
                  <span className="font-medium text-text-primary">
                    {p.symbol}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-data-mono">{p.quantity}</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-data-mono">{fmt(p.avgPrice)}</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-data-mono">{fmt(p.lastPrice)}</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-data-mono">¥{fmt(marketValue)}</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className={`text-data-mono ${pnlClass}`}>
                    {pnl >= 0 ? "+" : ""}
                    {fmt(pnl)}
                  </span>
                </TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}
