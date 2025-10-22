/**
 * 回测状态徽标组件
 *
 * 依据回测任务状态展示带颜色的 Badge。
 * 颜色全部来自 Design Tokens。
 */

import { cn, transitionClass } from "@qp/ui";
import type { BacktestStatus } from "@qp/api-client";

export interface BacktestStatusBadgeProps {
  status: BacktestStatus;
  className?: string;
}

const statusLabels: Record<BacktestStatus, string> = {
  pending: "排队中",
  running: "运行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

const statusStyles: Record<BacktestStatus, string> = {
  pending: "bg-secondary-300/20 text-text-secondary",
  running: "bg-primary-500/15 text-primary-700",
  completed: "bg-primary-500/10 text-primary-900",
  failed: "bg-state-risk/15 text-state-risk",
  cancelled: "bg-bg-subtle text-text-muted",
};

export function BacktestStatusBadge({
  status,
  className,
}: BacktestStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-sm text-caption font-medium whitespace-nowrap",
        transitionClass,
        statusStyles[status] ?? statusStyles.pending,
        className,
      )}
    >
      {statusLabels[status] ?? status}
    </span>
  );
}
