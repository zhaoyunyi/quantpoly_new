/**
 * Strategy Management Pages Tests
 *
 * 覆盖：
 * 7.1 列表页筛选/分页参数正确传递 API
 * 7.2 删除 409 STRATEGY_IN_USE 显示回测占用提示
 * 7.3 向导完整流程（模板选择 → 填参 → 确认创建）
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppProviders, bootstrapApiClient } from "../../../app/entry_wiring";

vi.mock("@qp/shell/redirect", () => ({
  redirectTo: vi.fn(),
}));

// 页面组件会使用 useNavigate（依赖 RouterProvider），但本测试只关心数据加载与 UI 行为；
// 因此在单测中将 useNavigate mock 成 noop，避免引入整套路由初始化。
vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-router")>(
    "@tanstack/react-router",
  );
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

/* ─── helpers ─── */

function mockEnvelope<T>(data: T) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve({ success: true, message: "ok", data }),
  };
}

function mockError(code: string, message: string, status = 409) {
  return {
    ok: false,
    status,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve({ success: false, error: { code, message } }),
  };
}

const meData = {
  id: "u-1",
  email: "u1@test.com",
  displayName: "U1",
  isActive: true,
  emailVerified: true,
  role: "user",
  level: 1,
};

const TEMPLATES = [
  {
    templateId: "tpl-ma-cross",
    name: "均线交叉",
    requiredParameters: {
      shortPeriod: { type: "integer", min: 1, max: 200 },
      longPeriod: { type: "integer", min: 2, max: 500 },
    },
    defaults: { shortPeriod: 5, longPeriod: 20 },
  },
  {
    templateId: "tpl-rsi",
    name: "RSI 反转",
    requiredParameters: {
      period: { type: "integer", min: 2, max: 100 },
    },
    defaults: { period: 14 },
  },
];

const STRATEGY_LIST = {
  items: [
    {
      id: "s-1",
      name: "MA策略",
      template: "tpl-ma-cross",
      status: "active",
      createdAt: "2026-01-01T00:00:00Z",
      updatedAt: "2026-01-02T00:00:00Z",
    },
    {
      id: "s-2",
      name: "RSI策略",
      template: "tpl-rsi",
      status: "draft",
      createdAt: "2026-01-03T00:00:00Z",
      updatedAt: "2026-01-04T00:00:00Z",
    },
    {
      id: "s-3",
      name: "已归档策略",
      template: "tpl-ma-cross",
      status: "archived",
      createdAt: "2026-01-05T00:00:00Z",
      updatedAt: "2026-01-06T00:00:00Z",
    },
  ],
  total: 3,
  page: 1,
  pageSize: 20,
};

describe("/strategies (列表页)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("given_list_data_when_render_then_shows_strategies_with_status_badges", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/strategies") && !url.includes("/templates")) {
        return Promise.resolve(mockEnvelope(STRATEGY_LIST));
      }
      if (url.includes("/templates"))
        return Promise.resolve(mockEnvelope(TEMPLATES));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/strategies/index");
    render(
      <AppProviders>
        <mod.StrategiesListPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("MA策略")).toBeInTheDocument();
    });

    expect(screen.getByText("RSI策略")).toBeInTheDocument();
    expect(screen.getByText("已归档策略")).toBeInTheDocument();
    expect(screen.getByText("运行中")).toBeInTheDocument();
    expect(screen.getByText("草稿")).toBeInTheDocument();
    expect(screen.getByText("已归档")).toBeInTheDocument();
  });

  it("given_search_and_status_filter_when_applied_then_api_receives_correct_params", async () => {
    const fetchCalls: string[] = [];
    const mockFetch = vi.fn((url: string) => {
      fetchCalls.push(url);
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/strategies") && !url.includes("/templates")) {
        return Promise.resolve(
          mockEnvelope({ ...STRATEGY_LIST, items: [], total: 0 }),
        );
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/strategies/index");
    const user = userEvent.setup();
    render(
      <AppProviders>
        <mod.StrategiesListPage />
      </AppProviders>,
    );

    // 等待初始加载
    await waitFor(() => {
      expect(fetchCalls.some((u) => u.includes("/strategies"))).toBe(true);
    });

    // 验证初始请求包含 page & pageSize
    const initialCall = fetchCalls.find(
      (u) => u.includes("/strategies") && !u.includes("/templates"),
    );
    expect(initialCall).toBeDefined();
    expect(initialCall).toContain("page=1");
    expect(initialCall).toContain("pageSize=20");

    // 等待页面主体渲染完成（AuthGuard 通过）
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "策略管理" }),
      ).toBeInTheDocument();
      expect(screen.getByLabelText("状态")).toBeInTheDocument();
    });

    // 应用 status 筛选（立即触发请求）
    await user.click(screen.getByLabelText("状态"));
    await user.click(screen.getByRole("option", { name: "草稿" }));

    await waitFor(() => {
      expect(
        fetchCalls.some(
          (u) =>
            u.includes("/strategies?") &&
            u.includes("status=draft") &&
            u.includes("page=1") &&
            u.includes("pageSize=20"),
        ),
      ).toBe(true);
    });

    // 应用 search（debounce 触发请求）
    await user.type(screen.getByLabelText("搜索"), "RSI");

    await waitFor(
      () => {
        expect(
          fetchCalls.some(
            (u) =>
              u.includes("/strategies?") &&
              u.includes("status=draft") &&
              u.includes("search=RSI") &&
              u.includes("page=1") &&
              u.includes("pageSize=20"),
          ),
        ).toBe(true);
      },
      { timeout: 1500 },
    );
  });

  it("given_strategy_in_use_when_delete_then_shows_backtest_conflict_error", async () => {
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (
        url.includes("/strategies") &&
        !url.includes("/templates") &&
        (!opts || opts.method === "GET" || !opts.method)
      ) {
        return Promise.resolve(mockEnvelope(STRATEGY_LIST));
      }
      if (url.includes("/templates"))
        return Promise.resolve(mockEnvelope(TEMPLATES));
      // DELETE 请求返回 409
      if (opts?.method === "DELETE") {
        return Promise.resolve(
          mockError("STRATEGY_IN_USE", "策略有正在运行的回测"),
        );
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/strategies/index");
    render(
      <AppProviders>
        <mod.StrategiesListPage />
      </AppProviders>,
    );

    // 等待列表渲染
    await waitFor(() => {
      expect(screen.getByText("RSI策略")).toBeInTheDocument();
    });

    const rsiRow = screen.getByText("RSI策略").closest("tr");
    expect(rsiRow).not.toBeNull();

    await user.click(within(rsiRow!).getByRole("button", { name: "删除" }));

    // 确认对话框
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "确认删除" }),
      ).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: "确认删除" });
    await user.click(confirmBtn);

    // 409 错误提示
    await waitFor(() => {
      expect(
        screen.getByText(/回测任务.*无法删除|回测占用/),
      ).toBeInTheDocument();
    });
  });
});

describe("/strategies/simple (向导)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_templates_when_complete_wizard_then_creates_strategy_successfully", async () => {
    const createdStrategy = {
      id: "s-new",
      name: "我的MA策略",
      template: "tpl-ma-cross",
      status: "draft",
      createdAt: "2026-01-10T00:00:00Z",
      updatedAt: "2026-01-10T00:00:00Z",
    };

    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/templates"))
        return Promise.resolve(mockEnvelope(TEMPLATES));
      // 从模板创建策略
      if (
        url.includes("/strategies/from-template") &&
        opts?.method === "POST"
      ) {
        return Promise.resolve(mockEnvelope(createdStrategy));
      }
      throw new Error(`unexpected: ${url} ${opts?.method}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/strategies/simple");
    render(
      <AppProviders>
        <mod.StrategySimplePage />
      </AppProviders>,
    );

    // Step 1: 等待模板加载 & 选择模板
    await waitFor(() => {
      expect(screen.getByText("均线交叉")).toBeInTheDocument();
    });

    await user.click(screen.getByText("均线交叉"));

    // Step 2: 填写参数
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /配置参数/ }),
      ).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText("策略名称");
    await user.clear(nameInput);
    await user.type(nameInput, "我的MA策略");

    const nextBtn = screen.getByRole("button", { name: "下一步" });
    await user.click(nextBtn);

    // Step 3: 确认创建
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "确认创建" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("我的MA策略")).toBeInTheDocument();
    expect(screen.getByText("均线交叉")).toBeInTheDocument();

    const createBtn = screen.getByRole("button", { name: "确认创建" });
    await user.click(createBtn);

    // 成功后展示选项
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /创建成功/ }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: "查看详情" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "立即回测" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "返回列表" }),
    ).toBeInTheDocument();
  });

  it("given_validation_error_when_create_then_returns_to_param_step", async () => {
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/templates"))
        return Promise.resolve(mockEnvelope(TEMPLATES));
      if (
        url.includes("/strategies/from-template") &&
        opts?.method === "POST"
      ) {
        return Promise.resolve({
          ok: false,
          status: 422,
          headers: new Headers({ "content-type": "application/json" }),
          json: () =>
            Promise.resolve({
              success: false,
              error: {
                code: "VALIDATION_ERROR",
                message: "parameter: shortPeriod must be >= 1",
              },
            }),
        });
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/strategies/simple");
    render(
      <AppProviders>
        <mod.StrategySimplePage />
      </AppProviders>,
    );

    // 选择模板
    await waitFor(() => {
      expect(screen.getByText("均线交叉")).toBeInTheDocument();
    });
    await user.click(screen.getByText("均线交叉"));

    // 填写名称
    await waitFor(() => {
      expect(screen.getByLabelText("策略名称")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("策略名称"), "Bad Strategy");
    await user.click(screen.getByRole("button", { name: "下一步" }));

    // 确认 → 创建
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "确认创建" }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "确认创建" }));

    // 验证：应回到参数步骤（step=1），并显示参数配置
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /配置参数/ }),
      ).toBeInTheDocument();
    });
  });
});
