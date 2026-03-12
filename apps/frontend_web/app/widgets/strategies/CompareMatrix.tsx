/**
 * 多策略对比矩阵组件
 *
 * 将 2-5 个策略的回测指标并列展示，方便横向对比。
 */

import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  Skeleton,
} from "@qp/ui";

export interface CompareMetricRow {
  label: string;
  values: string[];
}

export interface CompareMatrixProps {
  strategyNames: string[];
  metrics: CompareMetricRow[];
  loading?: boolean;
}

export function CompareMatrix({
  strategyNames,
  metrics,
  loading,
}: CompareMatrixProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-sm">
        {Array.from({ length: 6 }).map((_, idx) => (
          <Skeleton key={idx} width="100%" height="36px" />
        ))}
      </div>
    );
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>指标</TableHeaderCell>
          {strategyNames.map((name) => (
            <TableHeaderCell key={name}>{name}</TableHeaderCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {metrics.map((row) => (
          <TableRow key={row.label}>
            <TableCell>
              <span className="text-body font-medium">{row.label}</span>
            </TableCell>
            {row.values.map((val, idx) => (
              <TableCell key={idx}>
                <span className="text-data-mono">{val}</span>
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
