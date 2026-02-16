/**
 * ThemePreferencesForm — 主题偏好表单
 *
 * 主题模式（light/dark）和主色调写入 preferences.theme，
 * 通过 Design Tokens 层映射到组件，不直接写组件色值。
 */

import { useState } from "react";
import { Button } from "@qp/ui";
import { cn, transitionClass } from "@qp/ui";
import type { UserPreferences } from "@qp/api-client";

/* ─── 类型 ─── */

export interface ThemePreferencesFormProps {
  preferences: UserPreferences;
  onPatch: (patch: Record<string, unknown>) => Promise<void>;
  saving: boolean;
}

type ThemeMode = "light" | "dark";

interface ThemeState {
  mode: ThemeMode;
  primaryColor: string;
  darkMode: boolean;
}

/* ─── 常量 ─── */

const THEME_MODES: { value: ThemeMode; label: string; icon: string }[] = [
  { value: "light", label: "浅色模式", icon: "☀️" },
  { value: "dark", label: "深色模式", icon: "🌙" },
];

const PRIMARY_COLORS: { value: string; label: string; swatch: string }[] = [
  { value: "#1677ff", label: "默认蓝", swatch: "#1677ff" },
  { value: "#2D5990", label: "靛蓝", swatch: "#2D5990" },
  { value: "#4A7DB8", label: "天蓝", swatch: "#4A7DB8" },
  { value: "#6374A5", label: "冷紫", swatch: "#6374A5" },
  { value: "#1B3255", label: "深蓝", swatch: "#1B3255" },
];

/* ─── 组件 ─── */

export function ThemePreferencesForm({
  preferences,
  onPatch,
  saving,
}: ThemePreferencesFormProps) {
  const themePrefs = (preferences.theme ?? {}) as Record<string, unknown>;
  const currentDarkMode = (themePrefs.darkMode as boolean) ?? false;
  const currentPrimaryColor = (themePrefs.primaryColor as string) ?? "#1677ff";

  // 从 darkMode boolean 推断当前模式
  const initialMode: ThemeMode = currentDarkMode ? "dark" : "light";

  const [theme, setTheme] = useState<ThemeState>({
    mode: initialMode,
    primaryColor: currentPrimaryColor,
    darkMode: currentDarkMode,
  });

  const hasChanges =
    theme.primaryColor !== currentPrimaryColor ||
    theme.darkMode !== currentDarkMode;

  function handleModeChange(mode: ThemeMode) {
    const darkMode = mode === "dark";
    setTheme((prev) => ({ ...prev, mode, darkMode }));
  }

  function handleColorChange(color: string) {
    setTheme((prev) => ({ ...prev, primaryColor: color }));
  }

  async function handleSave() {
    if (!hasChanges) return;
    await onPatch({
      theme: {
        primaryColor: theme.primaryColor,
        darkMode: theme.darkMode,
      },
    });
  }

  return (
    <div className="flex flex-col gap-lg">
      {/* 主题模式选择 */}
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <h3 className="text-title-card mb-md">主题模式</h3>
        <p className="text-body-secondary mb-md">
          选择应用的外观模式。当前深色模式仅作为偏好记录，前端 UI
          暂未适配深色样式。
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-sm">
          {THEME_MODES.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleModeChange(opt.value)}
              className={cn(
                "flex flex-col items-center gap-sm p-md rounded-md border-2",
                transitionClass,
                theme.mode === opt.value
                  ? "border-primary-700 bg-primary-700/5"
                  : "border-secondary-300/30 bg-bg-card hover:border-secondary-300/60",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
              )}
            >
              <span className="text-2xl">{opt.icon}</span>
              <span
                className={cn(
                  "text-body font-medium",
                  theme.mode === opt.value
                    ? "text-primary-700"
                    : "text-text-primary",
                )}
              >
                {opt.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 主色调选择 */}
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <h3 className="text-title-card mb-md">主色调</h3>
        <p className="text-body-secondary mb-md">
          选择应用的品牌主色。颜色仅作为偏好持久化，实际呈现取决于 Design Tokens
          层。
        </p>
        <div className="flex flex-wrap gap-md">
          {PRIMARY_COLORS.map((color) => (
            <button
              key={color.value}
              type="button"
              onClick={() => handleColorChange(color.value)}
              title={color.label}
              className={cn(
                "flex flex-col items-center gap-xs",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40 rounded-md p-sm",
              )}
            >
              <span
                className={cn(
                  "block w-10 h-10 rounded-full border-2",
                  transitionClass,
                  theme.primaryColor === color.value
                    ? "border-primary-700 ring-2 ring-primary-500/40 ring-offset-2"
                    : "border-secondary-300/40",
                )}
                style={{ backgroundColor: color.swatch }}
              />
              <span
                className={cn(
                  "text-caption",
                  theme.primaryColor === color.value
                    ? "text-primary-700 font-medium"
                    : "text-text-secondary",
                )}
              >
                {color.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 预览 */}
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <h3 className="text-title-card mb-md">预览</h3>
        <div className="flex items-center gap-lg">
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-muted">选中主色</span>
            <div className="flex items-center gap-sm">
              <span
                className="block w-6 h-6 rounded-sm"
                style={{ backgroundColor: theme.primaryColor }}
              />
              <span className="text-data-mono">{theme.primaryColor}</span>
            </div>
          </div>
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-muted">深色模式</span>
            <span className="text-body">
              {theme.darkMode ? "开启" : "关闭"}
            </span>
          </div>
        </div>
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
          onClick={() =>
            setTheme({
              mode: initialMode,
              primaryColor: currentPrimaryColor,
              darkMode: currentDarkMode,
            })
          }
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
          保存主题
        </Button>
      </div>
    </div>
  );
}
