/**
 * CashFlowTable — 资金流水列表
 *
 * 展示充值、提现、买入、卖出等资金变动记录。
 */

import type { CashFlow } from "@qp/api-client";
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
} from "@qp/ui";

export interface CashFlowTableProps {
  flows: CashFlow[];
  loading?: boolean;
}

const FLOW_LABEL: Record<string, string> = {
  deposit: "充值",
  withdraw: "提现",
  trade_buy: "买入支出",
  trade_sell: "卖出收入",
};

function fmt(n: number): string {
  return n.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function CashFlowTable({ flows, loading }: CashFlowTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>类型</TableHeaderCell>
          <TableHeaderCell className="text-right">金额</TableHeaderCell>
          <TableHeaderCell>时间</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {flows.length === 0 && !loading ? (
          <TableEmpty colSpan={3} message="暂无资金流水" />
        ) : (
          flows.map((f) => (
            <TableRow key={f.id}>
              <TableCell>
                <span className="text-body text-text-primary">
                  {FLOW_LABEL[f.flowType] ?? f.flowType}
                </span>
              </TableCell>
              <TableCell className="text-right">
                <span
                  className={`text-data-mono ${f.amount >= 0 ? "state-up" : "state-down"}`}
                >
                  {f.amount >= 0 ? "+" : ""}
                  {fmt(f.amount)}
                </span>
              </TableCell>
              <TableCell>
                <span className="text-caption text-text-muted">
                  {new Date(f.createdAt).toLocaleString("zh-CN")}
                </span>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}
