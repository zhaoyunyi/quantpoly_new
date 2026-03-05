/**
 * UI Design System — TextField / Input
 *
 * 交互状态：default / hover / focus / disabled / error
 * 支持 label、错误提示、帮助文本。
 *
 * 全部样式来自 Design Tokens。
 */

import {
  type InputHTMLAttributes,
  type ReactNode,
  forwardRef,
  useId,
} from "react";
import { cn, transitionClass } from "./utils";

export interface TextFieldProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "size"
> {
  /** 字段标签 */
  label?: string;
  /** 帮助文本 */
  help?: string;
  /** 错误信息 */
  error?: string;
  /** 尺寸 */
  size?: "sm" | "md";
  /** 左侧图标/前缀 */
  startAdornment?: ReactNode;
  /** 右侧图标/后缀 */
  endAdornment?: ReactNode;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  (
    {
      label,
      help,
      error,
      size = "md",
      disabled,
      className,
      startAdornment,
      endAdornment,
      id: propId,
      ...props
    },
    ref,
  ) => {
    const autoId = useId();
    const id = propId ?? autoId;
    const errorId = `${id}-error`;
    const helpId = `${id}-help`;
    const hasError = !!error;

    return (
      <div className={cn("flex flex-col gap-1.5", className)}>
        {label && (
          <label
            htmlFor={id}
            className="text-body font-medium text-text-primary"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {startAdornment && (
            <span className="absolute left-3 text-text-muted pointer-events-none">
              {startAdornment}
            </span>
          )}
          <input
            ref={ref}
            id={id}
            disabled={disabled}
            aria-invalid={hasError}
            aria-describedby={
              [hasError ? errorId : "", help ? helpId : ""]
                .filter(Boolean)
                .join(" ") || undefined
            }
            className={cn(
              "w-full bg-bg-card border rounded-sm text-text-primary placeholder:text-text-muted",
              transitionClass,
              // 尺寸
              size === "sm" ? "h-8 px-3 text-caption" : "h-10 px-3 text-body",
              // 状态
              hasError
                ? "border-state-risk focus:ring-2 focus:ring-state-risk/30"
                : "border-secondary-300/40 focus:ring-2 focus:ring-primary-500/40",
              "focus:outline-none focus:ring-offset-1",
              disabled && "opacity-40 cursor-not-allowed bg-bg-subtle",
              startAdornment && "pl-9",
              endAdornment && "pr-9",
            )}
            {...props}
          />
          {endAdornment && (
            <span className="absolute right-3 text-text-muted pointer-events-none">
              {endAdornment}
            </span>
          )}
        </div>
        {hasError && (
          <p id={errorId} className="text-caption text-state-risk" role="alert">
            {error}
          </p>
        )}
        {help && !hasError && (
          <p id={helpId} className="text-caption text-text-muted">
            {help}
          </p>
        )}
      </div>
    );
  },
);

TextField.displayName = "TextField";
