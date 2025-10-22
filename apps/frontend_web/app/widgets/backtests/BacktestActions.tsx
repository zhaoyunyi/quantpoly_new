/**
 * 回测操作按钮组
 *
 * 根据回测任务状态条件渲染可执行的操作按钮。
 * 操作：取消、重试、重命名、删除。
 */

import { useState, type ChangeEvent } from "react";
import { Button, Dialog, TextField } from "@qp/ui";
import type { BacktestStatus } from "@qp/api-client";

export interface BacktestActionsProps {
  taskId: string;
  status: BacktestStatus;
  displayName: string | null;
  onCancel?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onRename?: (taskId: string, newName: string) => void;
  onDelete?: (taskId: string) => void;
  /** 是否以紧凑内联模式渲染（表格行内） */
  inline?: boolean;
}

export function BacktestActions({
  taskId,
  status,
  displayName,
  onCancel,
  onRetry,
  onRename,
  onDelete,
  inline = false,
}: BacktestActionsProps) {
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState(displayName ?? "");

  const canCancel = status === "pending" || status === "running";
  const canRetry = status === "failed" || status === "cancelled";
  const canDelete = status !== "running";

  const handleRenameSubmit = () => {
    if (renameValue.trim()) {
      onRename?.(taskId, renameValue.trim());
      setRenameOpen(false);
    }
  };

  const variant = inline ? ("ghost" as const) : ("secondary" as const);
  const size = inline ? ("sm" as const) : undefined;

  return (
    <>
      <div className="inline-flex items-center gap-1">
        {canCancel && (
          <Button
            variant={variant}
            size={size}
            onClick={() => onCancel?.(taskId)}
          >
            取消
          </Button>
        )}
        {canRetry && (
          <Button
            variant={variant}
            size={size}
            onClick={() => onRetry?.(taskId)}
          >
            重试
          </Button>
        )}
        <Button
          variant={variant}
          size={size}
          onClick={() => {
            setRenameValue(displayName ?? "");
            setRenameOpen(true);
          }}
        >
          重命名
        </Button>
        {canDelete && (
          <Button
            variant={variant}
            size={size}
            onClick={() => onDelete?.(taskId)}
          >
            删除
          </Button>
        )}
      </div>

      <Dialog
        open={renameOpen}
        onOpenChange={setRenameOpen}
        title="重命名回测"
        footer={
          <>
            <Button variant="secondary" onClick={() => setRenameOpen(false)}>
              取消
            </Button>
            <Button onClick={handleRenameSubmit}>确认</Button>
          </>
        }
      >
        <TextField
          label="显示名称"
          value={renameValue}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setRenameValue(e.target.value)
          }
          placeholder="输入新名称…"
        />
      </Dialog>
    </>
  );
}
