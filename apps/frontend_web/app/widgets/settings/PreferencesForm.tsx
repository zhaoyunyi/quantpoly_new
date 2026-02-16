/**
 * PreferencesForm — 偏好总览表单
 *
 * 以 JSON patch 语义展示和修改用户偏好子树。
 * 子域：通知 / 数据展示 / 同步。
 */

import { useState } from "react";
import { Button, Select, TextField } from "@qp/ui";
import type { UserPreferences } from "@qp/api-client";
import { cn, transitionClass } from "@qp/ui";

/* ─── 类型 ─── */

export interface PreferencesFormProps {
  preferences: UserPreferences;
  onPatch: (patch: Record<string, unknown>) => Promise<void>;
  saving: boolean;
}

/* ─── 常量 ─── */

const TIME_RANGE_OPTIONS = [
  { value: "1D", label: "1 天" },
  { value: "1W", label: "1 周" },
  { value: "1M", label: "1 个月" },
  { value: "3M", label: "3 个月" },
  { value: "6M", label: "6 个月" },
  { value: "1Y", label: "1 年" },
];

const REFRESH_INTERVAL_OPTIONS = [
  { value: "5s", label: "5 秒" },
  { value: "15s", label: "15 秒" },
  { value: "30s", label: "30 秒" },
  { value: "1m", label: "1 分钟" },
  { value: "5m", label: "5 分钟" },
];

const RISK_TOLERANCE_OPTIONS = [
  { value: "conservative", label: "保守" },
  { value: "moderate", label: "适中" },
  { value: "aggressive", label: "激进" },
];

const CURRENCY_OPTIONS = [
  { value: "USD", label: "USD" },
  { value: "CNY", label: "CNY" },
  { value: "EUR", label: "EUR" },
  { value: "JPY", label: "JPY" },
];

/* ─── 辅助函数 ─── */

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((cur, key) => {
    if (cur && typeof cur === "object")
      return (cur as Record<string, unknown>)[key];
    return undefined;
  }, obj);
}

function buildPatch(path: string, value: unknown): Record<string, unknown> {
  const keys = path.split(".");
  const result: Record<string, unknown> = {};
  let cursor = result;
  for (let i = 0; i < keys.length - 1; i++) {
    cursor[keys[i]] = {};
    cursor = cursor[keys[i]] as Record<string, unknown>;
  }
  cursor[keys[keys.length - 1]] = value;
  return result;
}

/* ─── 组件 ─── */

export function PreferencesForm({
  preferences,
  onPatch,
  saving,
}: PreferencesFormProps) {
  const [pendingPatches, setPendingPatches] = useState<Record<string, unknown>>(
    {},
  );
  const hasPending = Object.keys(pendingPatches).length > 0;

  function stage(path: string, value: unknown) {
    const patch = buildPatch(path, value);
    setPendingPatches((prev) => deepMergeLocal(prev, patch));
  }

  async function handleSave() {
    if (!hasPending) return;
    await onPatch(pendingPatches);
    setPendingPatches({});
  }

  // 合并 staged 值与 server 值
  function resolvedValue(path: string): unknown {
    const staged = getNestedValue(pendingPatches, path);
    if (staged !== undefined) return staged;
    return getNestedValue(preferences, path);
  }

  const account = preferences.account as Record<string, unknown> | undefined;
  const notifications = preferences.notifications as
    | Record<string, unknown>
    | undefined;
  const data = preferences.data as Record<string, unknown> | undefined;
  const emailNotif = (notifications?.email ?? {}) as Record<string, unknown>;
  const browserNotif = (notifications?.browser ?? {}) as Record<
    string,
    unknown
  >;
  const chartPrefs = (data?.chartPreferences ?? {}) as Record<string, unknown>;
  const tablePrefs = (data?.tablePreferences ?? {}) as Record<string, unknown>;

  return (
    <div className="flex flex-col gap-lg">
      {/* 账户偏好 */}
      <Section title="账户偏好">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <Select
            label="风险偏好"
            options={RISK_TOLERANCE_OPTIONS}
            value={
              (resolvedValue("account.riskTolerance") as string) ?? "moderate"
            }
            onValueChange={(v: string) => stage("account.riskTolerance", v)}
          />
          <Select
            label="默认货币"
            options={CURRENCY_OPTIONS}
            value={
              (resolvedValue("account.defaultCurrency") as string) ?? "USD"
            }
            onValueChange={(v: string) => stage("account.defaultCurrency", v)}
          />
          <ToggleRow
            label="自动选择账户"
            checked={
              (resolvedValue("account.autoSelectAccount") as boolean) ?? true
            }
            onChange={(v) => stage("account.autoSelectAccount", v)}
          />
        </div>
      </Section>

      {/* 通知偏好 */}
      <Section title="邮件通知">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <ToggleRow
            label="启用邮件通知"
            checked={
              (resolvedValue("notifications.email.enabled") as boolean) ?? true
            }
            onChange={(v) => stage("notifications.email.enabled", v)}
          />
          <ToggleRow
            label="交易提醒"
            checked={
              (resolvedValue("notifications.email.tradingAlerts") as boolean) ??
              true
            }
            onChange={(v) => stage("notifications.email.tradingAlerts", v)}
          />
          <ToggleRow
            label="风控提醒"
            checked={
              (resolvedValue("notifications.email.riskAlerts") as boolean) ??
              true
            }
            onChange={(v) => stage("notifications.email.riskAlerts", v)}
          />
          <ToggleRow
            label="系统更新"
            checked={
              (resolvedValue("notifications.email.systemUpdates") as boolean) ??
              false
            }
            onChange={(v) => stage("notifications.email.systemUpdates", v)}
          />
        </div>
      </Section>

      <Section title="浏览器通知">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <ToggleRow
            label="启用浏览器通知"
            checked={
              (resolvedValue("notifications.browser.enabled") as boolean) ??
              true
            }
            onChange={(v) => stage("notifications.browser.enabled", v)}
          />
          <ToggleRow
            label="交易信号"
            checked={
              (resolvedValue(
                "notifications.browser.tradingSignals",
              ) as boolean) ?? true
            }
            onChange={(v) => stage("notifications.browser.tradingSignals", v)}
          />
          <ToggleRow
            label="风险预警"
            checked={
              (resolvedValue(
                "notifications.browser.riskWarnings",
              ) as boolean) ?? true
            }
            onChange={(v) => stage("notifications.browser.riskWarnings", v)}
          />
        </div>
      </Section>

      {/* 数据展示偏好 */}
      <Section title="数据展示">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
          <Select
            label="默认时间范围"
            options={TIME_RANGE_OPTIONS}
            value={(resolvedValue("data.defaultTimeRange") as string) ?? "1M"}
            onValueChange={(v: string) => stage("data.defaultTimeRange", v)}
          />
          <Select
            label="刷新间隔"
            options={REFRESH_INTERVAL_OPTIONS}
            value={(resolvedValue("data.refreshInterval") as string) ?? "5s"}
            onValueChange={(v: string) => stage("data.refreshInterval", v)}
          />
          <ToggleRow
            label="显示成交量"
            checked={
              (resolvedValue("data.chartPreferences.showVolume") as boolean) ??
              true
            }
            onChange={(v) => stage("data.chartPreferences.showVolume", v)}
          />
          <ToggleRow
            label="显示指标"
            checked={
              (resolvedValue(
                "data.chartPreferences.showIndicators",
              ) as boolean) ?? false
            }
            onChange={(v) => stage("data.chartPreferences.showIndicators", v)}
          />
          <ToggleRow
            label="自动缩放"
            checked={
              (resolvedValue("data.chartPreferences.autoScale") as boolean) ??
              true
            }
            onChange={(v) => stage("data.chartPreferences.autoScale", v)}
          />
        </div>
      </Section>

      {/* 操作栏 */}
      <div className="flex items-center justify-end gap-sm pt-md border-t border-secondary-300/20">
        {hasPending && (
          <span className="text-caption text-text-muted mr-auto">
            有未保存的更改
          </span>
        )}
        <Button
          variant="secondary"
          size="sm"
          disabled={!hasPending || saving}
          onClick={() => setPendingPatches({})}
        >
          放弃
        </Button>
        <Button
          variant="primary"
          size="sm"
          disabled={!hasPending}
          loading={saving}
          onClick={handleSave}
        >
          保存更改
        </Button>
      </div>
    </div>
  );
}

/* ─── 内部子组件 ─── */

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-md">
      <h3 className="text-title-card mb-md">{title}</h3>
      {children}
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-md cursor-pointer select-none py-1">
      <span className="text-body text-text-primary">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full border-2 border-transparent",
          transitionClass,
          checked ? "bg-primary-700" : "bg-secondary-300/60",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40 focus-visible:ring-offset-1",
        )}
      >
        <span
          className={cn(
            "pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm",
            transitionClass,
            checked ? "translate-x-5" : "translate-x-0.5",
          )}
        />
      </button>
    </label>
  );
}

/* ─── 本地深合并 ─── */

function deepMergeLocal(
  base: Record<string, unknown>,
  patch: Record<string, unknown>,
): Record<string, unknown> {
  const result: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(patch)) {
    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      result[key] &&
      typeof result[key] === "object" &&
      !Array.isArray(result[key])
    ) {
      result[key] = deepMergeLocal(
        result[key] as Record<string, unknown>,
        value as Record<string, unknown>,
      );
    } else {
      result[key] = value;
    }
  }
  return result;
}
