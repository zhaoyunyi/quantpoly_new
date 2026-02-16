/**
 * AccountProfileForm — 账户资料表单
 *
 * 展示与修改当前用户的 email/displayName。
 * 通过 `PATCH /users/me` 持久化变更。
 */

import { type ChangeEvent, useState } from "react";
import { Button, TextField } from "@qp/ui";
import type { UserProfile } from "@qp/api-client";

/* ─── 类型 ─── */

export interface AccountProfileFormProps {
  profile: UserProfile;
  onUpdate: (updates: {
    email?: string;
    displayName?: string;
  }) => Promise<void>;
  saving: boolean;
}

/* ─── 组件 ─── */

export function AccountProfileForm({
  profile,
  onUpdate,
  saving,
}: AccountProfileFormProps) {
  const [email, setEmail] = useState(profile.email);
  const [displayName, setDisplayName] = useState(profile.displayName ?? "");
  const [emailError, setEmailError] = useState("");

  const hasChanges =
    email !== profile.email || displayName !== (profile.displayName ?? "");

  function validateEmail(value: string): boolean {
    if (!value.trim()) {
      setEmailError("邮箱不能为空");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      setEmailError("请输入有效的邮箱地址");
      return false;
    }
    setEmailError("");
    return true;
  }

  async function handleSave() {
    if (!validateEmail(email)) return;
    const updates: { email?: string; displayName?: string } = {};
    if (email !== profile.email) updates.email = email.trim();
    if (displayName !== (profile.displayName ?? ""))
      updates.displayName = displayName.trim() || undefined;
    if (Object.keys(updates).length === 0) return;
    await onUpdate(updates);
  }

  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
      <h3 className="text-title-card mb-md">个人资料</h3>
      <div className="flex flex-col gap-md">
        {/* 只读信息 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <ReadOnlyField label="用户 ID" value={profile.id} />
          <ReadOnlyField
            label="角色"
            value={profile.role === "admin" ? "管理员" : "普通用户"}
          />
          <ReadOnlyField
            label="邮箱已验证"
            value={profile.emailVerified ? "是" : "否"}
          />
          <ReadOnlyField
            label="账户状态"
            value={profile.isActive ? "活跃" : "已停用"}
          />
        </div>

        <div className="border-t border-secondary-300/20 pt-md" />

        {/* 可编辑字段 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <TextField
            label="邮箱"
            type="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => {
              setEmail(e.target.value);
              if (emailError) validateEmail(e.target.value);
            }}
            error={emailError}
          />
          <TextField
            label="显示名称"
            value={displayName}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setDisplayName(e.target.value)
            }
            placeholder="设置显示名称（可选）"
          />
        </div>

        {/* 操作栏 */}
        <div className="flex items-center justify-end gap-sm pt-md border-t border-secondary-300/20">
          {hasChanges && (
            <span className="text-caption text-text-muted mr-auto">
              有未保存的更改
            </span>
          )}
          <Button
            variant="secondary"
            size="sm"
            disabled={!hasChanges || saving}
            onClick={() => {
              setEmail(profile.email);
              setDisplayName(profile.displayName ?? "");
              setEmailError("");
            }}
          >
            放弃
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={!hasChanges}
            loading={saving}
            onClick={handleSave}
          >
            保存资料
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── 内部子组件 ─── */

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-body font-medium text-text-primary">{label}</span>
      <span className="h-10 flex items-center px-3 bg-bg-subtle border border-secondary-300/20 rounded-sm text-body text-text-secondary">
        {value}
      </span>
    </div>
  );
}
