/**
 * /settings — 偏好总览页
 *
 * 功能：
 * - 展示用户偏好（通知/数据/账户等子域）
 * - Patch 更新偏好
 * - 重置偏好为默认值
 * - 导出/导入偏好配置
 * - 子页面导航（主题、账户安全）
 */

import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useRef, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getPreferences,
  patchPreferences,
  resetPreferences,
  exportPreferences,
  importPreferences,
} from "@qp/api-client";
import type { UserPreferences, AppError } from "@qp/api-client";
import { Button, Dialog, Skeleton, useToast } from "@qp/ui";
import { useLoadable } from "../../shared/useLoadable";
import { PreferencesForm } from "../../widgets/settings/PreferencesForm";

export const Route = createFileRoute("/settings/")({
  component: SettingsPage,
});

/* ─── 子页面导航项 ─── */

const SETTINGS_NAV = [
  { label: "偏好设置", path: "/settings", active: true },
  { label: "主题外观", path: "/settings/theme", active: false },
  { label: "账户安全", path: "/settings/account", active: false },
];

export function SettingsPage() {
  const toast = useToast();
  const prefs = useLoadable<UserPreferences>(getPreferences);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ─── 偏好 Patch ─── */

  const handlePatch = useCallback(
    async (patch: Record<string, unknown>) => {
      setSaving(true);
      try {
        await patchPreferences(patch);
        toast.show("偏好已更新", "success");
        await prefs.reload();
      } catch (err) {
        toast.show((err as AppError).message || "保存失败", "error");
      } finally {
        setSaving(false);
      }
    },
    [prefs, toast],
  );

  /* ─── 重置 ─── */

  const handleReset = useCallback(async () => {
    setResetting(true);
    try {
      await resetPreferences();
      toast.show("偏好已重置为默认值", "success");
      await prefs.reload();
    } catch (err) {
      toast.show((err as AppError).message || "重置失败", "error");
    } finally {
      setResetting(false);
      setResetDialogOpen(false);
    }
  }, [prefs, toast]);

  /* ─── 导出 ─── */

  const handleExport = useCallback(async () => {
    try {
      const data = await exportPreferences();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `quantpoly-preferences-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.show("偏好配置已导出", "success");
    } catch (err) {
      toast.show((err as AppError).message || "导出失败", "error");
    }
  }, [toast]);

  /* ─── 导入 ─── */

  const handleImportClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setImporting(true);
      try {
        const text = await file.text();
        const data = JSON.parse(text) as Record<string, unknown>;
        await importPreferences(data);
        toast.show("偏好配置已导入", "success");
        await prefs.reload();
      } catch (err) {
        const message =
          err instanceof SyntaxError
            ? "文件格式无效，请上传 JSON 文件"
            : (err as AppError).message || "导入失败";
        toast.show(message, "error");
      } finally {
        setImporting(false);
        // 重置 input 以允许再次选择同一文件
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [prefs, toast],
  );

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 页面标题 */}
        <header>
          <h1 className="text-title-page">设置</h1>
          <p className="text-body-secondary mt-xs">
            管理你的个人偏好、主题与账户资料。
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

        {/* 工具栏 */}
        <div className="flex items-center gap-sm flex-wrap">
          <Button variant="secondary" size="sm" onClick={handleExport}>
            导出配置
          </Button>
          <Button
            variant="secondary"
            size="sm"
            loading={importing}
            onClick={handleImportClick}
          >
            导入配置
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={handleFileChange}
          />
          <div className="flex-1" />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setResetDialogOpen(true)}
            className="text-state-risk"
          >
            重置为默认
          </Button>
        </div>

        {/* 内容区 */}
        {prefs.loading ? (
          <LoadingSkeleton />
        ) : prefs.error ? (
          <ErrorCard
            message={prefs.error.message}
            onRetry={() => void prefs.reload()}
          />
        ) : prefs.data ? (
          <PreferencesForm
            preferences={prefs.data}
            onPatch={handlePatch}
            saving={saving}
          />
        ) : null}

        {/* 免责声明 */}
        <p className="text-disclaimer text-text-muted mt-lg">
          偏好设置仅影响界面展示与通知行为，不构成投资建议。
        </p>
      </div>

      {/* 重置确认对话框 */}
      <Dialog
        open={resetDialogOpen}
        onOpenChange={setResetDialogOpen}
        title="确认重置偏好"
        description="此操作将把所有偏好恢复为系统默认值，已自定义的配置将丢失。"
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setResetDialogOpen(false)}
              disabled={resetting}
            >
              取消
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={resetting}
              onClick={handleReset}
            >
              确认重置
            </Button>
          </>
        }
      >
        <p className="text-body text-text-primary">
          重置后，通知、数据展示、账户偏好等所有自定义设置将恢复为系统默认值。
          此操作可通过导入之前导出的配置来恢复。
        </p>
      </Dialog>
    </ProtectedLayout>
  );
}

/* ─── 内部组件 ─── */

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-lg">
      {Array.from({ length: 3 }).map((_, idx) => (
        <div
          key={idx}
          className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md"
        >
          <Skeleton width="30%" height="18px" />
          <div className="mt-md grid grid-cols-2 gap-md">
            {Array.from({ length: 4 }).map((_, j) => (
              <Skeleton key={j} width="100%" height="40px" />
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
      <p className="text-body text-text-primary mb-sm">偏好加载失败</p>
      <p className="text-body-secondary mb-md">
        {message || "无法获取偏好数据，请稍后重试。"}
      </p>
      <Button variant="secondary" size="sm" onClick={onRetry}>
        重试
      </Button>
    </div>
  );
}
