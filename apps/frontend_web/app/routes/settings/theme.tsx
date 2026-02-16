/**
 * /settings/theme — 主题偏好页
 *
 * 功能：
 * - 主题模式选择（light/dark）
 * - 主色调选择
 * - 写入 preferences.theme
 */

import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import { getPreferences, patchPreferences } from "@qp/api-client";
import type { UserPreferences, AppError } from "@qp/api-client";
import { Button, Skeleton, useToast } from "@qp/ui";
import { useLoadable } from "../../shared/useLoadable";
import { ThemePreferencesForm } from "../../widgets/settings/ThemePreferencesForm";

export const Route = createFileRoute("/settings/theme")({
  component: ThemePage,
});

/* ─── 子页面导航项 ─── */

const SETTINGS_NAV = [
  { label: "偏好设置", path: "/settings", active: false },
  { label: "主题外观", path: "/settings/theme", active: true },
  { label: "账户安全", path: "/settings/account", active: false },
];

export function ThemePage() {
  const toast = useToast();
  const prefs = useLoadable<UserPreferences>(getPreferences);
  const [saving, setSaving] = useState(false);

  const handlePatch = useCallback(
    async (patch: Record<string, unknown>) => {
      setSaving(true);
      try {
        await patchPreferences(patch);
        toast.show("主题偏好已更新", "success");
        await prefs.reload();
      } catch (err) {
        toast.show((err as AppError).message || "保存失败", "error");
      } finally {
        setSaving(false);
      }
    },
    [prefs, toast],
  );

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 页面标题 */}
        <header>
          <h1 className="text-title-page">主题外观</h1>
          <p className="text-body-secondary mt-xs">
            自定义应用的外观模式与品牌色调。
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

        {/* 内容区 */}
        {prefs.loading ? (
          <LoadingSkeleton />
        ) : prefs.error ? (
          <ErrorCard
            message={prefs.error.message}
            onRetry={() => void prefs.reload()}
          />
        ) : prefs.data ? (
          <ThemePreferencesForm
            preferences={prefs.data}
            onPatch={handlePatch}
            saving={saving}
          />
        ) : null}

        {/* 免责声明 */}
        <p className="text-disclaimer text-text-muted mt-lg">
          主题偏好仅影响界面外观，不构成投资建议。
        </p>
      </div>
    </ProtectedLayout>
  );
}

/* ─── 内部组件 ─── */

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-lg">
      {Array.from({ length: 2 }).map((_, idx) => (
        <div
          key={idx}
          className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md"
        >
          <Skeleton width="25%" height="18px" />
          <div className="mt-md flex flex-wrap gap-md">
            {Array.from({ length: 3 }).map((_, j) => (
              <Skeleton key={j} width="120px" height="80px" />
            ))}
          </div>
        </div>
      ))}
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
      <p className="text-body text-text-primary mb-sm">主题偏好加载失败</p>
      <p className="text-body-secondary mb-md">
        {message || "无法获取偏好数据。"}
      </p>
      <Button variant="secondary" size="sm" onClick={onRetry}>
        重试
      </Button>
    </div>
  );
}
