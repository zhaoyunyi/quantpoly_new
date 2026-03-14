/**
 * UI Design System — Table
 *
 * 可组合式 Table 组件。
 * 支持斑马纹（交替行背景）、排序指示器、空状态。
 * 全部样式来自 Design Tokens。
 */

import {
  type ReactNode,
  type ThHTMLAttributes,
  type TdHTMLAttributes,
} from "react";
import { cn, transitionClass } from "./utils";

/* ─── Table Root ─── */

export interface TableProps {
  children: ReactNode;
  className?: string;
}

export function Table({ children, className }: TableProps) {
  return (
    <div
      className={cn(
        "overflow-x-auto rounded-md border border-secondary-300/20",
        className,
      )}
    >
      <table className="w-full border-collapse text-body">{children}</table>
    </div>
  );
}

/* ─── Table Head ─── */

export function TableHead({ children, className }: TableProps) {
  return (
    <thead
      className={cn("bg-bg-subtle border-b border-secondary-300/20", className)}
    >
      {children}
    </thead>
  );
}

/* ─── Table Body ─── */

export function TableBody({ children, className }: TableProps) {
  return (
    <tbody className={cn("[&>tr:nth-child(even)]:bg-bg-subtle/50", className)}>
      {children}
    </tbody>
  );
}

/* ─── Table Row ─── */

export function TableRow({
  children,
  className,
  ...props
}: TableProps & React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        "border-b border-secondary-300/10 last:border-b-0",
        "hover:bg-bg-subtle/70",
        transitionClass,
        className,
      )}
      {...props}
    >
      {children}
    </tr>
  );
}

/* ─── Table Header Cell ─── */

export interface TableHeaderCellProps extends ThHTMLAttributes<HTMLTableCellElement> {
  className?: string;
  children?: ReactNode;
  sortable?: boolean;
  sortDirection?: "asc" | "desc" | null;
}

export function TableHeaderCell({
  children,
  sortable,
  sortDirection,
  className,
  ...props
}: TableHeaderCellProps) {
  return (
    <th
      className={cn(
        "px-md py-sm text-left text-caption font-medium text-text-secondary whitespace-nowrap",
        sortable && "cursor-pointer select-none hover:text-text-primary",
        className,
      )}
      aria-sort={
        sortDirection === "asc"
          ? "ascending"
          : sortDirection === "desc"
            ? "descending"
            : undefined
      }
      {...props}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {sortable && sortDirection && (
          <span className="text-text-muted" aria-hidden="true">
            {sortDirection === "asc" ? "↑" : "↓"}
          </span>
        )}
      </span>
    </th>
  );
}

/* ─── Table Cell ─── */

export function TableCell({
  children,
  className,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement> & { children?: ReactNode }) {
  return (
    <td
      className={cn("px-md py-sm text-body text-text-primary", className)}
      {...props}
    >
      {children}
    </td>
  );
}

/* ─── Empty State ─── */

export interface TableEmptyProps {
  colSpan: number;
  message?: string;
  children?: ReactNode;
}

export function TableEmpty({
  colSpan,
  message = "暂无数据",
  children,
}: TableEmptyProps) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-md py-2xl text-center">
        <div className="flex flex-col items-center gap-sm text-text-muted">
          <svg
            width="40"
            height="40"
            viewBox="0 0 40 40"
            fill="none"
            aria-hidden="true"
            className="opacity-40"
          >
            <rect
              x="4"
              y="8"
              width="32"
              height="24"
              rx="4"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path d="M4 16h32" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <p className="text-body-secondary">{message}</p>
          {children}
        </div>
      </td>
    </tr>
  );
}
