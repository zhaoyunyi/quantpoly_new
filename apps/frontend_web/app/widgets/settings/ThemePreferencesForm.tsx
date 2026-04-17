/**
 * ThemePreferencesForm — 主题偏好表单
 *
 * 主题模式通过 ThemeProvider (useTheme) 即时切换，同时持久化到后端 preferences。
 * 主色调选择器引用 Design Token 语义名，不使用 HEX 字面值。
 */

import { useEffect, useState } from "react";
import { Button, useTheme } from "@qp/ui";
import { cn, transitionClass } from "@qp/ui";
import { Sun, Moon, Monitor, type LucideIcon } from "lucide-react";
import type { UserPreferences } from "@qp/api-client";

/* ─── 类型 ─── */

export interface ThemePreferencesFormProps {
  preferences: UserPreferences;
  onPatch: (patch: Record<string, unknown>) => Promise<void>;
  saving: boolean;
}

type ThemeMode = "light" | "dark" | "system";

/* ─── 常量 ─── */

const THEME_MODES: { value: ThemeMode; label: string; icon: LucideIcon }[] = [
  { value: "light", label: "浅色模式", icon: Sun },
  { value: "dark", label: "深色模式", icon: Moon },
  { value: "system", label: "跟随系统", icon: Monitor },
];

interface PrimaryColorOption {
  token: string;
  label: string;
  cssVar: string;
}

const PRIMARY_COLORS: PrimaryColorOption[] = [
  { token: "primary-700", label: "靛蓝", cssVar: "var(--color-primary-700)" },
  { token: "primary-500", label: "天蓝", cssVar: "var(--color-primary-500)" },
  { token: "primary-900", label: "深蓝", cssVar: "var(--color-primary-900)" },
  { token: "secondary-500", label: "冷紫", cssVar: "var(--color-secondary-500)" },
];

/* ─── 组件 ─── */

export function ThemePreferencesForm({
  preferences,
  onPatch,
  saving,
}: ThemePreferencesFormProps) {
  const { theme: currentTheme, setTheme: applyTheme } = useTheme();

  const themePrefs = (preferences.theme ?? {}) as Record<string, unknown>;
  const savedMode =
    ((themePrefs.mode as ThemeMode | undefined) ??
      ((themePrefs.darkMode as boolean | undefined) === true ? "dark" : "light")) as ThemeMode;
  const savedPrimaryToken = (themePrefs.primaryColor as string) ?? "primary-700";

  const [selectedColor, setSelectedColor] = useState(savedPrimaryToken);

  const hasColorChange = selectedColor !== savedPrimaryToken;

  useEffect(() => {
    if (currentTheme !== savedMode) {
      applyTheme(savedMode);
    }
  }, [applyTheme, currentTheme, savedMode]);

  useEffect(() => {
    setSelectedColor(savedPrimaryToken);
  }, [savedPrimaryToken]);

  function handleModeChange(mode: ThemeMode) {
    applyTheme(mode);
    void onPatch({ theme: { mode } });
  }

  async function handleSaveColor() {
    if (!hasColorChange) return;
    await onPatch({ theme: { mode: currentTheme, primaryColor: selectedColor } });
  }

  return (
    <div className="flex flex-col gap-lg">
      {/* 主题模式选择 */}
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
        <h3 className="text-title-card mb-md">主题模式</h3>
        <p className="text-body-secondary mb-md">
          选择应用的外观模式，切换即时生效。
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
                currentTheme === opt.value
                  ? "border-primary-700 bg-primary-700/5"
                  : "border-secondary-300/30 bg-bg-card hover:border-secondary-300/60",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
              )}
            >
              <opt.icon className="size-6" aria-hidden="true" />
              <span
                className={cn(
                  "text-body font-medium",
                  currentTheme === opt.value
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
          选择应用的品牌主色。颜色通过 Design Token 语义名引用。
        </p>
        <div className="flex flex-wrap gap-md">
          {PRIMARY_COLORS.map((color) => (
            <button
              key={color.token}
              type="button"
              onClick={() => setSelectedColor(color.token)}
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
                  selectedColor === color.token
                    ? "border-primary-700 ring-2 ring-primary-500/40 ring-offset-2"
                    : "border-secondary-300/40",
                )}
                style={{ backgroundColor: color.cssVar }}
              />
              <span
                className={cn(
                  "text-caption",
                  selectedColor === color.token
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
                style={{
                  backgroundColor:
                    PRIMARY_COLORS.find((c) => c.token === selectedColor)
                      ?.cssVar ?? "var(--color-primary-700)",
                }}
              />
              <span className="text-data-mono">{selectedColor}</span>
            </div>
          </div>
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-muted">主题模式</span>
            <span className="text-body">{currentTheme}</span>
          </div>
        </div>
      </div>

      {/* 操作栏 — 仅主色调需要手动保存，模式切换即时生效 */}
      {hasColorChange && (
        <div className="flex items-center justify-end gap-sm pt-md border-t border-secondary-300/20">
          <span className="text-caption text-text-muted mr-auto">
            主色调有未保存的更改
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={saving}
            onClick={() => setSelectedColor(savedPrimaryToken)}
          >
            放弃
          </Button>
          <Button
            variant="primary"
            size="sm"
            loading={saving}
            onClick={handleSaveColor}
          >
            保存主色调
          </Button>
        </div>
      )}
    </div>
  );
}
