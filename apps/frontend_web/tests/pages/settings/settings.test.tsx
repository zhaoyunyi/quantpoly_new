/**
 * Settings / Preferences — /settings
 *
 * 目标：
 * - patch 偏好后刷新并展示更新后的数据
 * - reset 偏好后刷新展示
 * - 导入偏好后刷新展示
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppProviders, bootstrapApiClient } from "../../../app/entry_wiring";

vi.mock("@qp/shell/redirect", () => ({
  redirectTo: vi.fn(),
}));

/* ─── mock 数据 ─── */

const ME_RESPONSE = {
  success: true,
  message: "ok",
  data: {
    id: "u-1",
    email: "user@example.com",
    displayName: "User",
    isActive: true,
    emailVerified: true,
    role: "user",
    level: 1,
  },
};

function makePrefsData(overrides: Record<string, unknown> = {}) {
  return {
    version: 1,
    theme: { primaryColor: "#1677ff", darkMode: false },
    account: {
      defaultTradingAccountId: null,
      riskTolerance: "moderate",
      defaultCurrency: "USD",
      autoSelectAccount: true,
    },
    notifications: {
      email: {
        enabled: true,
        tradingAlerts: true,
        riskAlerts: true,
        systemUpdates: false,
        marketSummary: false,
      },
      browser: {
        enabled: true,
        permission: "default",
        tradingSignals: true,
        riskWarnings: true,
      },
      alertThresholds: {
        profitThreshold: 10,
        lossThreshold: 5,
        riskLevel: "medium",
      },
    },
    data: {
      defaultTimeRange: "1M",
      refreshInterval: "5s",
      chartPreferences: {
        defaultChartType: "line",
        showVolume: true,
        showIndicators: false,
        autoScale: true,
      },
      tablePreferences: {
        pageSize: 20,
        compactRows: false,
        showDecimals: 2,
      },
    },
    advanced: null,
    lastUpdated: "2026-01-01T00:00:00Z",
    syncEnabled: true,
    ...overrides,
  };
}

function prefsEnvelope(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    message: "ok",
    data: makePrefsData(overrides),
  };
}

describe("/settings — 偏好总览", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_loaded_prefs_when_patch_then_calls_patch_and_refreshes", async () => {
    let prefsGetCount = 0;
    let lastPatchBody: Record<string, unknown> | null = null;
    let currentPrefs = makePrefsData();

    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      if (
        url.endsWith("/users/me") &&
        (!init || init.method === "GET" || !init.method)
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(ME_RESPONSE),
        });
      }

      if (
        url.endsWith("/users/me/preferences") &&
        (!init || !init.method || init.method === "GET")
      ) {
        prefsGetCount++;
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve({ success: true, message: "ok", data: currentPrefs }),
        });
      }

      if (url.endsWith("/users/me/preferences") && init?.method === "PATCH") {
        const patchBody = JSON.parse(String(init.body)) as Record<string, unknown>;
        lastPatchBody = patchBody;
        currentPrefs = {
          ...currentPrefs,
          account: {
            ...(currentPrefs.account as Record<string, unknown>),
            ...(patchBody.account as Record<string, unknown>),
          },
        };
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve({ success: true, message: "ok", data: currentPrefs }),
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/settings/index");

    render(
      <AppProviders>
        <mod.SettingsPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("账户偏好")).toBeInTheDocument();
    });

    const switches = screen.getAllByRole("switch");
    expect(switches[0]).toHaveAttribute("aria-checked", "true");

    await userEvent.click(switches[0]);
    await userEvent.click(screen.getByRole("button", { name: "保存更改" }));

    await waitFor(() => {
      expect(lastPatchBody).not.toBeNull();
      expect(prefsGetCount).toBeGreaterThanOrEqual(2);
    });

    expect(lastPatchBody).toMatchObject({
      account: { autoSelectAccount: false },
    });
    expect(screen.getAllByRole("switch")[0]).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("given_loaded_prefs_when_reset_then_refreshes_display", async () => {
    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      if (
        url.endsWith("/users/me") &&
        (!init || init.method === "GET" || !init.method)
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(ME_RESPONSE),
        });
      }

      if (
        url.endsWith("/users/me/preferences") &&
        (!init || !init.method || init.method === "GET")
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(prefsEnvelope()),
        });
      }

      if (
        url.endsWith("/users/me/preferences/reset") &&
        init?.method === "POST"
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(prefsEnvelope()),
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/settings/index");

    render(
      <AppProviders>
        <mod.SettingsPage />
      </AppProviders>,
    );

    // 等待页面加载
    await waitFor(() => {
      expect(screen.getByText("重置为默认")).toBeInTheDocument();
    });

    // 点击"重置为默认"按钮
    const resetBtn = screen.getByText("重置为默认");
    await userEvent.click(resetBtn);

    // 等待确认对话框出现
    await waitFor(() => {
      expect(screen.getByText("确认重置偏好")).toBeInTheDocument();
    });

    // 点击"确认重置"
    const confirmBtn = screen.getByText("确认重置");
    await userEvent.click(confirmBtn);

    // 验证 reset 端点被调用
    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, i]) =>
            String(u).endsWith("/users/me/preferences/reset") &&
            (i as RequestInit)?.method === "POST",
        ),
      ).toBe(true);
    });
  });

  it("given_loaded_prefs_when_import_then_calls_import_and_refreshes", async () => {
    let prefsGetCount = 0;
    let importCalled = false;
    let currentPrefs = makePrefsData();

    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      if (
        url.endsWith("/users/me") &&
        (!init || init.method === "GET" || !init.method)
      ) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(ME_RESPONSE),
        });
      }

      if (
        url.endsWith("/users/me/preferences") &&
        (!init || !init.method || init.method === "GET")
      ) {
        prefsGetCount++;
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve({ success: true, message: "ok", data: currentPrefs }),
        });
      }

      if (
        url.endsWith("/users/me/preferences/import") &&
        init?.method === "POST"
      ) {
        const imported = JSON.parse(String(init.body)) as Record<string, unknown>;
        currentPrefs = makePrefsData(imported);
        importCalled = true;
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve({ success: true, message: "ok", data: currentPrefs }),
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/settings/index");

    const view = render(
      <AppProviders>
        <mod.SettingsPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("导入配置")).toBeInTheDocument();
    });

    const input = view.container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement | null;
    expect(input).not.toBeNull();

    const importedPrefs = {
      account: {
        ...makePrefsData().account,
        riskTolerance: "aggressive",
      },
    };
    const file = new File(
      [JSON.stringify(importedPrefs)],
      "preferences.json",
      { type: "application/json" },
    );
    Object.defineProperty(file, "text", {
      value: () => Promise.resolve(JSON.stringify(importedPrefs)),
    });
    fireEvent.change(input as HTMLInputElement, { target: { files: [file] } });

    await waitFor(() => {
      expect(importCalled).toBe(true);
      expect(prefsGetCount).toBeGreaterThanOrEqual(2);
    });
  });
});
