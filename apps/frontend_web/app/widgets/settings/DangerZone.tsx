/**
 * DangerZone — 危险操作区域
 *
 * 改密 + 注销账户。
 * 注销需要二次确认对话框（输入 "DELETE" 后方可提交）。
 */

import { type ChangeEvent, useState } from "react";
import { Button, Dialog, TextField } from "@qp/ui";

/* ─── 类型 ─── */

export interface DangerZoneProps {
  onChangePassword: (payload: {
    currentPassword: string;
    newPassword: string;
    revokeAllSessions: boolean;
  }) => Promise<void>;
  onDeleteAccount: () => Promise<void>;
  changingPassword: boolean;
  deletingAccount: boolean;
}

/* ─── 常量 ─── */

const DELETE_CONFIRM_TEXT = "DELETE";

/* ─── 组件 ─── */

export function DangerZone({
  onChangePassword,
  onDeleteAccount,
  changingPassword,
  deletingAccount,
}: DangerZoneProps) {
  return (
    <div className="flex flex-col gap-lg">
      <ChangePasswordSection
        onSubmit={onChangePassword}
        loading={changingPassword}
      />
      <DeleteAccountSection
        onSubmit={onDeleteAccount}
        loading={deletingAccount}
      />
    </div>
  );
}

/* ─── 改密 ─── */

function ChangePasswordSection({
  onSubmit,
  loading,
}: {
  onSubmit: DangerZoneProps["onChangePassword"];
  loading: boolean;
}) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [revokeAll, setRevokeAll] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!current) errs.current = "请输入当前密码";
    if (!next) errs.next = "请输入新密码";
    else if (next.length < 8) errs.next = "新密码至少 8 位";
    if (next !== confirm) errs.confirm = "两次输入的密码不一致";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    try {
      await onSubmit({
        currentPassword: current,
        newPassword: next,
        revokeAllSessions: revokeAll,
      });
    } catch {
      return;
    }
    setCurrent("");
    setNext("");
    setConfirm("");
    setRevokeAll(false);
    setErrors({});
  }

  return (
    <div className="bg-bg-card rounded-md shadow-card border border-state-risk/20 p-md">
      <h3 className="text-title-card mb-xs">修改密码</h3>
      <p className="text-body-secondary mb-md">
        修改后当前会话保留，可选择是否注销所有其他会话。
      </p>
      <div className="flex flex-col gap-md max-w-md">
        <TextField
          label="当前密码"
          type="password"
          value={current}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setCurrent(e.target.value)
          }
          error={errors.current}
          autoComplete="current-password"
        />
        <TextField
          label="新密码"
          type="password"
          value={next}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setNext(e.target.value)
          }
          error={errors.next}
          help="至少 8 位，建议包含大小写字母和数字"
          autoComplete="new-password"
        />
        <TextField
          label="确认新密码"
          type="password"
          value={confirm}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setConfirm(e.target.value)
          }
          error={errors.confirm}
          autoComplete="new-password"
        />
        <label className="flex items-center gap-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={revokeAll}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setRevokeAll(e.target.checked)
            }
            className="w-4 h-4 accent-primary-700"
          />
          <span className="text-body text-text-primary">注销所有其他会话</span>
        </label>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            size="sm"
            loading={loading}
            disabled={!current || !next || !confirm}
            onClick={handleSubmit}
          >
            修改密码
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── 注销账户 ─── */

function DeleteAccountSection({
  onSubmit,
  loading,
}: {
  onSubmit: () => Promise<void>;
  loading: boolean;
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  const canDelete = confirmText === DELETE_CONFIRM_TEXT;

  async function handleDelete() {
    if (!canDelete) return;
    try {
      await onSubmit();
    } catch {
      return;
    }
    setDialogOpen(false);
    setConfirmText("");
  }

  return (
    <>
      <div className="bg-bg-card rounded-md shadow-card border border-state-risk/30 p-md">
        <h3 className="text-title-card mb-xs state-risk">注销账户</h3>
        <p className="text-body-secondary mb-md">
          注销账户将永久删除所有数据（策略、回测、交易记录等），此操作不可撤销。
        </p>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setDialogOpen(true)}
          className="border-state-risk/40 text-state-risk hover:bg-state-risk/5"
        >
          注销我的账户
        </Button>
      </div>

      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setConfirmText("");
        }}
        title="确认注销账户"
        description="此操作不可撤销。注销后您的所有数据将被永久删除。"
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setDialogOpen(false)}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={!canDelete}
              loading={loading}
              onClick={handleDelete}
              className="bg-state-risk hover:bg-state-risk/90"
            >
              确认注销
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-md">
          <p className="text-body text-text-primary">
            请输入{" "}
            <strong className="font-medium text-state-risk">
              {DELETE_CONFIRM_TEXT}
            </strong>{" "}
            以确认注销：
          </p>
          <TextField
            value={confirmText}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setConfirmText(e.target.value)
            }
            placeholder={`请输入 ${DELETE_CONFIRM_TEXT}`}
            error={
              confirmText && !canDelete
                ? `请输入 "${DELETE_CONFIRM_TEXT}" 以确认`
                : undefined
            }
          />
        </div>
      </Dialog>
    </>
  );
}
