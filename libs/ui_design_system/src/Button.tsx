/**
 * UI Design System — Button
 *
 * 交互状态：default / hover / focus / disabled / loading
 * 变体：primary / secondary / ghost
 * 尺寸：sm / md / lg
 *
 * 全部样式来自 Design Tokens，禁止硬编码颜色。
 */

import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn, focusRingClass, disabledClass, transitionClass } from "./utils";

export type ButtonVariant = "primary" | "secondary" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    "bg-primary-700 text-white",
    "hover:opacity-92",
    "active:bg-primary-900",
  ].join(" "),
  secondary: [
    "bg-bg-subtle text-text-primary border border-secondary-300/40",
    "hover:opacity-92",
    "active:bg-bg-page",
  ].join(" "),
  ghost: [
    "bg-transparent text-primary-700",
    "hover:bg-bg-subtle hover:opacity-92",
    "active:bg-bg-subtle",
  ].join(" "),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-caption gap-1.5 rounded-sm",
  md: "h-10 px-4 text-body gap-2 rounded-sm",
  lg: "h-12 px-6 text-body gap-2.5 rounded-sm font-medium",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        type="button"
        disabled={isDisabled}
        className={cn(
          // 基础
          "inline-flex items-center justify-center font-medium select-none",
          transitionClass,
          // 变体
          variantStyles[variant],
          // 尺寸
          sizeStyles[size],
          // 焦点
          "focus-visible:" + focusRingClass.split(" ").join(" focus-visible:"),
          // 禁用
          isDisabled && disabledClass,
          className,
        )}
        aria-busy={loading}
        aria-disabled={isDisabled}
        {...props}
      >
        {loading && <Spinner className="shrink-0" />}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";

/* ─── 内置 Loading Spinner ─── */

function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin h-4 w-4", className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        className="opacity-20"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
