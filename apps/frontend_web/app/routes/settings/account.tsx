/**
 * /settings/account — 账户资料与安全页
 *
 * 功能：
 * - 资料读取与更新（email/displayName）
 * - 修改密码
 * - 注销账户（二次确认）
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getMe,
  updateMe,
  changePassword,
  deleteAccount,
  logout,
} from "@qp/api-client";
import type { UserProfile, AppError } from "@qp/api-client";
import { Button, Skeleton, useToast } from "@qp/ui";
import { useLoadable } from "../../shared/useLoadable";
import { AccountProfileForm } from "../../widgets/settings/AccountProfileForm";
import { DangerZone } from "../../widgets/settings/DangerZone";

export const Route = createFileRoute("/settings/account")({
  component: AccountPage,
});

/* ─── 子页面导航项 ─── */

const SETTINGS_NAV = [
  { label: "偏好设置", path: "/settings", active: false },
  { label: "主题外观", path: "/settings/theme", active: false },
  { label: "账户安全", path: "/settings/account", active: true },
];

export function AccountPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const profile = useLoadable<UserProfile>(getMe);
  const [savingProfile, setSavingProfile] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);

  /* ─── 资料更新 ─── */

  const handleUpdateProfile = useCallback(
    async (updates: { email?: string; displayName?: string }) => {
      setSavingProfile(true);
      try {
        await updateMe(updates);
        toast.show("资料已更新", "success");
        await profile.reload();
      } catch (err) {
        toast.show((err as AppError).message || "更新失败", "error");
      } finally {
        setSavingProfile(false);
      }
    },
    [profile, toast],
  );

  /* ─── 改密 ─── */

  const handleChangePassword = useCallback(
    async (payload: {
      currentPassword: string;
      newPassword: string;
      revokeAllSessions: boolean;
    }) => {
      setChangingPassword(true);
      try {
        const result = await changePassword({
          currentPassword: payload.currentPassword,
          newPassword: payload.newPassword,
          revokeAllSessions: payload.revokeAllSessions,
        });
        const msg = payload.revokeAllSessions
          ? `密码已修改，已注销 ${result.revokedSessions} 个其他会话`
          : "密码已修改";
        toast.show(msg, "success");
      } catch (err) {
        toast.show((err as AppError).message || "密码修改失败", "error");
        throw err;
      } finally {
        setChangingPassword(false);
      }
    },
    [toast],
  );

  /* ─── 注销账户 ─── */

  const handleDeleteAccount = useCallback(async () => {
    setDeletingAccount(true);
    try {
      await deleteAccount();
      toast.show("账户已注销", "success");
      // 注销后登出并跳转到登录页
      try {
        await logout();
      } catch {
        // 忽略 logout 失败（账户已删除，session 可能已失效）
      }
      navigate({ to: "/auth/login" });
    } catch (err) {
      toast.show((err as AppError).message || "注销失败", "error");
      throw err;
    } finally {
      setDeletingAccount(false);
    }
  }, [toast, navigate]);

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 页面标题 */}
        <header>
          <h1 className="text-title-page">账户安全</h1>
          <p className="text-body-secondary mt-xs">
            管理个人资料、密码与账户安全设置。
          </p>
        </header>

        {/* 子页面导航 */}
        <nav className="flex gap-sm border-b border-secondary-300/20 pb-0">
          {SETTINGS_NAV.map((item) => (
            <a
              key={item.path}
              href={item.path}
              className={[
                "px-md py-sm text-body font-medium border-b-2 -mb-px transition-colors duration-120",
                item.active
                  ? "border-primary-700 text-primary-700"
                  : "border-transparent text-text-secondary hover:text-text-primary hover:border-secondary-300/40",
              ].join(" ")}
            >
              {item.label}
            </a>
          ))}
        </nav>

        {/* 资料区 */}
        {profile.loading ? (
          <LoadingSkeleton />
        ) : profile.error ? (
          <ErrorCard
            message={profile.error.message}
            onRetry={() => void profile.reload()}
          />
        ) : profile.data ? (
          <>
            <AccountProfileForm
              profile={profile.data}
              onUpdate={handleUpdateProfile}
              saving={savingProfile}
            />
            <DangerZone
              onChangePassword={handleChangePassword}
              onDeleteAccount={handleDeleteAccount}
              changingPassword={changingPassword}
              deletingAccount={deletingAccount}
            />
          </>
        ) : null}

        {/* 免责声明 */}
        <p className="text-disclaimer text-text-muted mt-lg">
          账户注销操作不可撤销。请在操作前备份重要数据。
        </p>
      </div>
    </ProtectedLayout>
  );
}

/* ─── 内部组件 ─── */

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-lg">
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <Skeleton width="25%" height="18px" />
        <div className="mt-md grid grid-cols-2 gap-md">
          {Array.from({ length: 4 }).map((_, j) => (
            <div key={j} className="flex flex-col gap-1.5">
              <Skeleton width="60%" height="14px" />
              <Skeleton width="100%" height="40px" />
            </div>
          ))}
        </div>
      </div>
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <Skeleton width="20%" height="18px" />
        <div className="mt-md flex flex-col gap-md max-w-md">
          {Array.from({ length: 3 }).map((_, j) => (
            <Skeleton key={j} width="100%" height="40px" />
          ))}
        </div>
      </div>
    </div>
  );
}

function ErrorCard({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="bg-bg-card rounded-md shadow-card border border-state-risk/20 p-md text-center">
      <p className="text-body text-text-primary mb-sm">资料加载失败</p>
      <p className="text-body-secondary mb-md">
        {message || "无法获取账户资料。"}
      </p>
      <Button variant="secondary" size="sm" onClick={onRetry}>
        重试
      </Button>
    </div>
  );
}
