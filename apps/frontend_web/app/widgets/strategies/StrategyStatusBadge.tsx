/**
 * 策略状态徽标组件
 *
 * 依据策略当前状态展示带颜色的小型 Badge。
 * 颜色全部来自 Design Tokens。
 */

import { cn, transitionClass } from "@qp/ui";
import type { StrategyStatus } from "@qp/api-client";

export interface StrategyStatusBadgeProps {
  status: StrategyStatus;
  className?: string;
}

const statusLabels: Record<StrategyStatus, string> = {
  draft: "草稿",
  active: "运行中",
  inactive: "已停用",
  archived: "已归档",
};

const statusStyles: Record<StrategyStatus, string> = {
  draft: "bg-secondary-300/20 text-text-secondary",
  active: "bg-primary-500/15 text-primary-700",
  inactive: "bg-state-risk/15 text-state-risk",
  archived: "bg-bg-subtle text-text-muted",
};

export function StrategyStatusBadge({
  status,
  className,
}: StrategyStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-sm text-caption font-medium whitespace-nowrap",
        transitionClass,
        statusStyles[status] ?? statusStyles.draft,
        className,
      )}
    >
      {statusLabels[status] ?? status}
    </span>
  );
}
