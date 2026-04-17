/**
 * UI Design System — Skeleton / Spinner / EmptyState
 *
 * 加载状态占位组件。
 * 全部样式来自 Design Tokens。
 */

import { type ReactNode } from "react";
import { cn } from "./utils";

/* ─── Skeleton ─── */

export interface SkeletonProps {
  className?: string;
  /** 宽度（Tailwind class 或 inline） */
  width?: string;
  /** 高度（Tailwind class 或 inline） */
  height?: string;
  /** 是否为圆形 */
  circle?: boolean;
}

export function Skeleton({ className, width, height, circle }: SkeletonProps) {
  return (
    <div
      className={cn(
        "bg-bg-subtle animate-pulse",
        circle ? "rounded-full" : "rounded-sm",
        className,
      )}
      style={{
        width: width ?? "100%",
        height: height ?? "1em",
      }}
      role="status"
      aria-label="加载中"
    />
  );
}

/* ─── Spinner ─── */

export interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const spinnerSizes = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-10 w-10",
};

export function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <svg
      className={cn(
        "animate-spin text-primary-500",
        spinnerSizes[size],
        className,
      )}
      viewBox="0 0 24 24"
      fill="none"
      role="status"
      aria-label="加载中"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        className="opacity-20"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* ─── EmptyState ─── */

export interface EmptyStateProps {
  /** 空状态标题 */
  title?: string;
  /** 描述文案 */
  description?: string;
  /** 操作区（如按钮） */
  action?: ReactNode;
  /** 自定义图标 */
  icon?: ReactNode;
  /** 场景变体：first-use 首次使用 / no-results 无结果 / error 错误 */
  variant?: "first-use" | "no-results" | "error";
  className?: string;
}

const VARIANT_ICONS: Record<
  NonNullable<EmptyStateProps["variant"]>,
  ReactNode
> = {
  "first-use": (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      className="text-text-muted mb-md"
      aria-hidden="true"
    >
      <path
        d="M20 4l3 8h8l-6.5 5 2.5 8L20 19.5 13 25l2.5-8L9 12h8l3-8z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M20 30v6M14 33l1.5-2M26 33l-1.5-2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  ),
  "no-results": (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      className="text-text-muted mb-md"
      aria-hidden="true"
    >
      <circle cx="18" cy="18" r="10" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M26 26l8 8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  ),
  error: (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      className="text-text-muted mb-md"
      aria-hidden="true"
    >
      <path
        d="M20 6L4 34h32L20 6z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M20 16v8M20 28h.01"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  ),
};

export function EmptyState({
  title = "暂无数据",
  description,
  action,
  icon,
  variant = "no-results",
  className,
}: EmptyStateProps) {
  const variantIcon = VARIANT_ICONS[variant];

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-2xl px-lg text-center",
        className,
      )}
    >
      {icon ?? variantIcon}
      <h3 className="text-title-card text-text-secondary">{title}</h3>
      {description && (
        <p className="text-body-secondary mt-xs max-w-sm">{description}</p>
      )}
      {action && <div className="mt-md">{action}</div>}
    </div>
  );
}
