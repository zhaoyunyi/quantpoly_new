/**
 * UI Design System — Select
 *
 * 基于 Base UI Select 的封装。
 * 交互状态：default / hover / focus / disabled / error
 * 全部样式来自 Design Tokens。
 */

import { type ReactNode, forwardRef, useId } from "react";
import { Select as BaseSelect } from "@base-ui/react/select";
import { cn, transitionClass } from "./utils";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  label?: string;
  options: SelectOption[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  error?: string;
  help?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export const Select = forwardRef<HTMLButtonElement, SelectProps>(
  (
    {
      label,
      options,
      value,
      defaultValue,
      onValueChange,
      placeholder = "请选择",
      error,
      help,
      disabled,
      className,
      id: propId,
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
        <BaseSelect.Root
          value={value}
          defaultValue={defaultValue}
          onValueChange={onValueChange}
          disabled={disabled}
        >
          <BaseSelect.Trigger
            ref={ref}
            id={id}
            aria-invalid={hasError}
            aria-describedby={
              [hasError ? errorId : "", help ? helpId : ""]
                .filter(Boolean)
                .join(" ") || undefined
            }
            className={cn(
              "flex items-center justify-between w-full h-10 px-3 bg-bg-card border rounded-sm text-body text-text-primary",
              transitionClass,
              hasError
                ? "border-state-risk focus:ring-2 focus:ring-state-risk/30"
                : "border-secondary-300/40 focus:ring-2 focus:ring-primary-500/40",
              "focus:outline-none focus:ring-offset-1",
              disabled && "opacity-40 cursor-not-allowed bg-bg-subtle",
            )}
          >
            <BaseSelect.Value placeholder={placeholder} />
            <BaseSelect.Icon className="text-text-muted">
              <ChevronDown />
            </BaseSelect.Icon>
          </BaseSelect.Trigger>

          <BaseSelect.Portal>
            <BaseSelect.Positioner sideOffset={4}>
              <BaseSelect.Popup
                className={cn(
                  "bg-bg-card border border-secondary-300/40 rounded-md shadow-card",
                  "py-1 min-w-[var(--anchor-width)]",
                  "origin-[var(--transform-origin)]",
                  transitionClass,
                )}
              >
                {options.map((opt) => (
                  <BaseSelect.Option
                    key={opt.value}
                    value={opt.value}
                    disabled={opt.disabled}
                    className={cn(
                      "flex items-center px-3 py-2 text-body text-text-primary cursor-pointer select-none",
                      "hover:bg-bg-subtle",
                      "data-[highlighted]:bg-bg-subtle",
                      "data-[selected]:text-primary-700 data-[selected]:font-medium",
                      opt.disabled && "opacity-40 cursor-not-allowed",
                    )}
                  >
                    <BaseSelect.OptionIndicator className="mr-2 text-primary-700">
                      ✓
                    </BaseSelect.OptionIndicator>
                    <BaseSelect.OptionText>{opt.label}</BaseSelect.OptionText>
                  </BaseSelect.Option>
                ))}
              </BaseSelect.Popup>
            </BaseSelect.Positioner>
          </BaseSelect.Portal>
        </BaseSelect.Root>

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

Select.displayName = "Select";

/* ─── 内置图标 ─── */

function ChevronDown() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M4 6l4 4 4-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
