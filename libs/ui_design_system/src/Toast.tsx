/**
 * UI Design System — Toast
 *
 * 最小实现：全局 Toast 容器 + 命令式 API。
 * 后续可替换为更成熟的方案。
 *
 * 全部样式来自 Design Tokens。
 */

import {
  createContext,
  useCallback,
  useContext,
  useState,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { cn, transitionClass } from "./utils";

/* ─── 类型 ─── */

export type ToastVariant = "info" | "success" | "error" | "warning";

export interface ToastItem {
  id: string;
  variant: ToastVariant;
  message: string;
  duration?: number;
}

export interface ToastAPI {
  show: (message: string, variant?: ToastVariant, duration?: number) => void;
  dismiss: (id: string) => void;
  dismissAll: () => void;
}

/* ─── Context ─── */

const ToastContext = createContext<ToastAPI | null>(null);

let _toastCounter = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const show = useCallback(
    (message: string, variant: ToastVariant = "info", duration = 4000) => {
      const id = `toast-${++_toastCounter}`;
      setToasts((prev) => [...prev, { id, variant, message, duration }]);
    },
    [],
  );

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ show, dismiss, dismissAll }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastAPI {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast 必须在 <ToastProvider> 内使用");
  }
  return ctx;
}

/* ─── Toast 容器 ─── */

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div
      aria-live="polite"
      aria-label="通知"
      className="fixed bottom-6 right-6 z-50 flex flex-col gap-sm max-w-sm"
    >
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

/* ─── 单条 Toast ─── */

const variantStyles: Record<ToastVariant, string> = {
  info: "border-l-primary-500",
  success: "border-l-state-down", // 绿色
  error: "border-l-state-up", // 红色
  warning: "border-l-state-risk",
};

const variantIcons: Record<ToastVariant, string> = {
  info: "ℹ",
  success: "✓",
  error: "✕",
  warning: "⚠",
};

function ToastCard({
  toast,
  onDismiss,
}: {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}) {
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const duration = toast.duration ?? 4000;
    if (duration > 0) {
      timerRef.current = setTimeout(() => onDismiss(toast.id), duration);
    }
    return () => clearTimeout(timerRef.current);
  }, [toast.id, toast.duration, onDismiss]);

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-sm p-md bg-bg-card rounded-md shadow-card border-l-4",
        variantStyles[toast.variant],
        transitionClass,
      )}
    >
      <span
        className="shrink-0 text-body font-medium mt-0.5"
        aria-hidden="true"
      >
        {variantIcons[toast.variant]}
      </span>
      <p className="text-body text-text-primary flex-1">{toast.message}</p>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className={cn(
          "shrink-0 p-0.5 rounded-sm text-text-muted hover:text-text-primary",
          transitionClass,
        )}
        aria-label="关闭通知"
      >
        <svg
          width="14"
          height="14"
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
      </button>
    </div>
  );
}
