/**
 * 策略列表表格组件
 *
 * 包含排序、行操作（查看/编辑/激活/停用/归档/删除）和空状态。
 * 全部样式来自 Design Tokens。
 */

import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
  Button,
} from "@qp/ui";
import { useState } from "react";
import type { StrategyItem } from "@qp/api-client";
import { StrategyStatusBadge } from "./StrategyStatusBadge";

export interface StrategyTableProps {
  items: StrategyItem[];
  loading?: boolean;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onActivate?: (id: string) => void | Promise<void>;
  onDeactivate?: (id: string) => void | Promise<void>;
  onArchive?: (id: string) => void | Promise<void>;
  onDelete?: (id: string) => void;
}

export function StrategyTable({
  items,
  loading,
  onView,
  onEdit,
  onActivate,
  onDeactivate,
  onArchive,
  onDelete,
}: StrategyTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>策略名称</TableHeaderCell>
          <TableHeaderCell>模板</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell>创建时间</TableHeaderCell>
          <TableHeaderCell>更新时间</TableHeaderCell>
          <TableHeaderCell className="text-right">操作</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {items.length === 0 && !loading ? (
          <TableEmpty colSpan={6} message="暂无策略数据。请先创建策略。" />
        ) : (
          items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                  <button
                    type="button"
                    className="text-primary-500 hover:text-primary-700 font-medium transition-all duration-120 ease-out text-left"
                    onClick={() => onView?.(item.id)}
                  >
                    {item.name}
                  </button>
              </TableCell>
              <TableCell>
                <span className="text-caption text-text-secondary">
                  {item.template}
                </span>
              </TableCell>
              <TableCell>
                <StrategyStatusBadge status={item.status} />
              </TableCell>
              <TableCell>
                <span className="text-data-mono">
                  {formatDate(item.createdAt)}
                </span>
              </TableCell>
              <TableCell>
                <span className="text-data-mono">
                  {formatDate(item.updatedAt)}
                </span>
              </TableCell>
              <TableCell className="text-right">
                <RowActions
                  item={item}
                  onView={onView}
                  onEdit={onEdit}
                  onActivate={onActivate}
                  onDeactivate={onDeactivate}
                  onArchive={onArchive}
                  onDelete={onDelete}
                />
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}

function RowActions({
  item,
  onView,
  onEdit,
  onActivate,
  onDeactivate,
  onArchive,
  onDelete,
}: {
  item: StrategyItem;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onActivate?: (id: string) => void | Promise<void>;
  onDeactivate?: (id: string) => void | Promise<void>;
  onArchive?: (id: string) => void | Promise<void>;
  onDelete?: (id: string) => void;
}) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const busy = busyAction !== null;

  const wrap = (action: string, fn?: (id: string) => void | Promise<void>) => {
    if (!fn) return undefined;
    return async () => {
      setBusyAction(action);
      try {
        await fn(item.id);
      } finally {
        setBusyAction(null);
      }
    };
  };

  return (
    <div className="inline-flex items-center gap-1">
      <Button variant="ghost" size="sm" disabled={busy} onClick={() => onView?.(item.id)}>
        查看
      </Button>
      {item.status !== "archived" && (
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => onEdit?.(item.id)}>
          编辑
        </Button>
      )}
      {(item.status === "draft" || item.status === "inactive") && (
        <Button
          variant="ghost"
          size="sm"
          loading={busyAction === "activate"}
          disabled={busy && busyAction !== "activate"}
          onClick={() => void wrap("activate", onActivate)?.()}
        >
          激活
        </Button>
      )}
      {item.status === "active" && (
        <Button
          variant="ghost"
          size="sm"
          loading={busyAction === "deactivate"}
          disabled={busy && busyAction !== "deactivate"}
          onClick={() => void wrap("deactivate", onDeactivate)?.()}
        >
          停用
        </Button>
      )}
      {item.status !== "archived" && (
        <Button
          variant="ghost"
          size="sm"
          loading={busyAction === "archive"}
          disabled={busy && busyAction !== "archive"}
          onClick={() => void wrap("archive", onArchive)?.()}
        >
          归档
        </Button>
      )}
      {item.status !== "archived" && (
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => onDelete?.(item.id)}>
          删除
        </Button>
      )}
    </div>
  );
}

function formatDate(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return isoStr;
  }
}
