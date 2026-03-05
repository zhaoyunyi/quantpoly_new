/**
 * UI Design System — Dialog / Modal
 *
 * 基于 Base UI Dialog 的封装。
 * 交互状态：open / close 动画、焦点管理、ESC 关闭。
 * 全部样式来自 Design Tokens。
 */

import { type ReactNode } from "react";
import { Dialog as BaseDialog } from "@base-ui/react/dialog";
import { cn, transitionClass } from "./utils";

export interface DialogProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onOpenChange: (open: boolean) => void;
  /** 对话框标题 */
  title: string;
  /** 对话框描述（可选） */
  description?: string;
  /** 内容 */
  children: ReactNode;
  /** 底部操作区 */
  footer?: ReactNode;
  /** 自定义内容区 className */
  className?: string;
}

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
}: DialogProps) {
  return (
    <BaseDialog.Root open={open} onOpenChange={onOpenChange}>
      <BaseDialog.Portal>
        <BaseDialog.Backdrop
          className={cn(
            "fixed inset-0 bg-text-primary/20 backdrop-blur-[2px]",
            transitionClass,
            "data-[starting-style]:opacity-0 data-[ending-style]:opacity-0",
          )}
        />
        <BaseDialog.Popup
          className={cn(
            "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
            "w-full max-w-lg bg-bg-card rounded-md shadow-card",
            "p-lg",
            transitionClass,
            "data-[starting-style]:opacity-0 data-[starting-style]:scale-95",
            "data-[ending-style]:opacity-0 data-[ending-style]:scale-95",
            className,
          )}
        >
          <BaseDialog.Title className="text-title-card">
            {title}
          </BaseDialog.Title>
          {description && (
            <BaseDialog.Description className="text-body-secondary mt-sm">
              {description}
            </BaseDialog.Description>
          )}
          <div className="mt-md">{children}</div>
          {footer && (
            <div className="flex items-center justify-end gap-sm mt-lg">
              {footer}
            </div>
          )}
          <BaseDialog.Close
            className={cn(
              "absolute top-3 right-3 p-1 rounded-sm text-text-muted",
              "hover:text-text-primary hover:bg-bg-subtle",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
              transitionClass,
            )}
            aria-label="关闭"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M4 4l8 8M12 4l-8 8"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </BaseDialog.Close>
        </BaseDialog.Popup>
      </BaseDialog.Portal>
    </BaseDialog.Root>
  );
}
