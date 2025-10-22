/**
 * 回测列表表格组件
 *
 * 展示回测任务列表，支持多选（用于对比）、行操作。
 * 全部样式来自 Design Tokens。
 */

import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
} from "@qp/ui";
import type { BacktestTask } from "@qp/api-client";
import { BacktestStatusBadge } from "./BacktestStatusBadge";
import { BacktestActions } from "./BacktestActions";

export interface BacktestTableProps {
  items: BacktestTask[];
  loading?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
  onView?: (id: string) => void;
  onCancel?: (id: string) => void;
  onRetry?: (id: string) => void;
  onRename?: (id: string, name: string) => void;
  onDelete?: (id: string) => void;
}

export function BacktestTable({
  items,
  loading,
  selectedIds,
  onToggleSelect,
  onView,
  onCancel,
  onRetry,
  onRename,
  onDelete,
}: BacktestTableProps) {
  const showSelect = !!onToggleSelect;

  return (
    <Table>
      <TableHead>
        <TableRow>
          {showSelect && <TableHeaderCell className="w-10" />}
          <TableHeaderCell>名称 / ID</TableHeaderCell>
          <TableHeaderCell>策略</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell>收益率</TableHeaderCell>
          <TableHeaderCell>最大回撤</TableHeaderCell>
          <TableHeaderCell>创建时间</TableHeaderCell>
          <TableHeaderCell className="text-right">操作</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {items.length === 0 && !loading ? (
          <TableEmpty
            colSpan={showSelect ? 8 : 7}
            message="暂无回测数据。请先创建回测任务。"
          />
        ) : (
          items.map((item) => {
            const isSelected = selectedIds?.has(item.id) ?? false;
            return (
              <TableRow key={item.id}>
                {showSelect && (
                  <TableCell>
                    <button
                      type="button"
                      onClick={() => onToggleSelect?.(item.id)}
                      className={`w-5 h-5 rounded-sm border flex items-center justify-center transition-all duration-120 ease-out ${
                        isSelected
                          ? "bg-primary-700 border-primary-700 text-white"
                          : "border-secondary-300/40"
                      }`}
                      aria-label={isSelected ? "取消选择" : "选择"}
                    >
                      {isSelected && (
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 16 16"
                          fill="none"
                          aria-hidden="true"
                        >
                          <path
                            d="M3 8l4 4 6-6"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </button>
                  </TableCell>
                )}
                <TableCell>
                  <button
                    type="button"
                    className="text-primary-500 hover:text-primary-700 font-medium transition-all duration-120 ease-out text-left"
                    onClick={() => onView?.(item.id)}
                  >
                    {item.displayName || truncateId(item.id)}
                  </button>
                  {item.displayName && (
                    <span className="block text-data-mono text-text-muted text-caption">
                      {truncateId(item.id)}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-data-mono text-caption text-text-secondary">
                    {truncateId(item.strategyId)}
                  </span>
                </TableCell>
                <TableCell>
                  <BacktestStatusBadge status={item.status} />
                </TableCell>
                <TableCell>
                  <span className="text-data-mono">
                    {formatMetric(item.metrics?.returnRate)}
                  </span>
                </TableCell>
                <TableCell>
                  <span
                    className={`text-data-mono ${
                      (item.metrics?.maxDrawdown ?? 0) > 0.2 ? "state-risk" : ""
                    }`}
                  >
                    {formatMetric(item.metrics?.maxDrawdown)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-data-mono">
                    {formatDate(item.createdAt)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <BacktestActions
                    taskId={item.id}
                    status={item.status}
                    displayName={item.displayName}
                    onCancel={onCancel}
                    onRetry={onRetry}
                    onRename={onRename}
                    onDelete={onDelete}
                    inline
                  />
                </TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}

function truncateId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 12)}…` : id;
}

function formatDate(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

function formatMetric(val: unknown): string {
  if (val === null || val === undefined) return "-";
  const num = Number(val);
  if (!Number.isFinite(num)) return "-";
  return `${(num * 100).toFixed(2)}%`;
}
