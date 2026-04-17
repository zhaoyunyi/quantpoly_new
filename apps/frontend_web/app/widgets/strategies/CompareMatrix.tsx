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
  /** 是否高亮最优/最差值，默认 true */
  highlightBestWorst?: boolean;
}

/** 指标名包含这些关键词时，越低越好 */
const LOWER_IS_BETTER_PATTERN = /drawdown|回撤|risk|风险/i;

function parseComparableNumber(value: string): number {
  return parseFloat(value.replace(/,/g, "").trim());
}

function getHighlightIndices(
  values: string[],
  lowerIsBetter: boolean,
): { bestIdx: number; worstIdx: number } | null {
  const parsed = values.map(parseComparableNumber);
  const validIndices = parsed
    .map((n, i) => (Number.isNaN(n) ? -1 : i))
    .filter((i) => i >= 0);
  if (validIndices.length < 2) return null;

  let bestIdx = validIndices[0];
  let worstIdx = validIndices[0];
  for (const i of validIndices) {
    if (lowerIsBetter) {
      if (parsed[i] < parsed[bestIdx]) bestIdx = i;
      if (parsed[i] > parsed[worstIdx]) worstIdx = i;
    } else {
      if (parsed[i] > parsed[bestIdx]) bestIdx = i;
      if (parsed[i] < parsed[worstIdx]) worstIdx = i;
    }
  }
  if (bestIdx === worstIdx) return null;
  return { bestIdx, worstIdx };
}

export function CompareMatrix({
  strategyNames,
  metrics,
  loading,
  highlightBestWorst = true,
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
        {metrics.map((row) => {
          const lowerIsBetter = LOWER_IS_BETTER_PATTERN.test(row.label);
          const hl =
            highlightBestWorst
              ? getHighlightIndices(row.values, lowerIsBetter)
              : null;

          return (
            <TableRow key={row.label}>
              <TableCell>
                <span className="text-body font-medium">{row.label}</span>
              </TableCell>
              {row.values.map((val, idx) => {
                let cls = "text-data-mono";
                if (hl) {
                  if (idx === hl.bestIdx)
                    cls = "text-data-mono text-state-up font-medium";
                  else if (idx === hl.worstIdx)
                    cls = "text-data-mono text-state-down";
                }
                return (
                  <TableCell key={idx}>
                    <span className={cls}>{val}</span>
                  </TableCell>
                );
              })}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
