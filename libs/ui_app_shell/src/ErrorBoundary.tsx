/**
 * App Shell — 全局错误边界
 *
 * route-level + app-level 错误捕获。
 */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { cn } from "@qp/ui";

export interface ErrorBoundaryProps {
  children: ReactNode;
  /** 自定义 fallback */
  fallback?: ReactNode;
  /** 错误上报回调 */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 错误上报
    console.error("[ErrorBoundary]", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={() => this.setState({ hasError: false, error: null })}
        />
      );
    }
    return this.props.children;
  }
}

/* ─── 默认错误 Fallback ─── */

function ErrorFallback({
  error,
  onRetry,
}: {
  error: Error | null;
  onRetry: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[400px] px-lg">
      <div className="max-w-md text-center">
        <div className="text-state-risk mb-md">
          <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            className="mx-auto"
            aria-hidden="true"
          >
            <circle
              cx="24"
              cy="24"
              r="20"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path
              d="M24 14v12m0 6h.01"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <h2 className="text-title-section mb-xs">页面出现异常</h2>
        <p className="text-body-secondary mb-md">
          {error?.message || "发生了未知错误，请刷新页面或稍后再试。"}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className={cn(
            "inline-flex items-center justify-center h-10 px-6 rounded-sm",
            "bg-primary-700 text-white font-medium",
            "hover:opacity-92 transition-all duration-[120ms] ease-out",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40 focus-visible:ring-offset-1",
          )}
        >
          重新加载
        </button>
      </div>
    </div>
  );
}
