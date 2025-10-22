/**
 * Backtest Center Pages Tests
 *
 * 覆盖：
 * 5.1 result 未就绪时展示"刷新/轮询"提示
 * 5.2 compare 选中数量与提交参数正确
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppProviders, bootstrapApiClient } from "../../../app/entry_wiring";

vi.mock("@qp/shell/redirect", () => ({
  redirectTo: vi.fn(),
}));

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

function mockErrorResponse(code: string, message: string, status = 404) {
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

const BACKTEST_LIST = {
  items: [
    {
      id: "bt-1",
      userId: "u-1",
      strategyId: "s-1",
      status: "completed",
      config: { startDate: "2025-01-01", endDate: "2025-12-31" },
      metrics: {
        returnRate: 0.1534,
        maxDrawdown: 0.0821,
        sharpeRatio: 1.42,
        tradeCount: 56,
        winRate: 0.62,
      },
      displayName: "MA均线回测",
      createdAt: "2026-01-10T10:00:00Z",
      updatedAt: "2026-01-10T12:00:00Z",
    },
    {
      id: "bt-2",
      userId: "u-1",
      strategyId: "s-1",
      status: "running",
      config: {},
      metrics: {},
      displayName: null,
      createdAt: "2026-01-11T10:00:00Z",
      updatedAt: "2026-01-11T10:05:00Z",
    },
    {
      id: "bt-3",
      userId: "u-1",
      strategyId: "s-2",
      status: "failed",
      config: {},
      metrics: {},
      displayName: "RSI回测",
      createdAt: "2026-01-12T10:00:00Z",
      updatedAt: "2026-01-12T10:30:00Z",
    },
  ],
  total: 3,
  page: 1,
  pageSize: 20,
};

const BACKTEST_STATISTICS = {
  pendingCount: 0,
  runningCount: 1,
  completedCount: 1,
  failedCount: 1,
  cancelledCount: 0,
  totalCount: 3,
  averageReturnRate: 0.1534,
  averageMaxDrawdown: 0.0821,
  averageWinRate: 0.62,
};

describe("/backtests (列表页)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("given_list_data_when_render_then_shows_backtests_with_status_badges", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/backtests/statistics"))
        return Promise.resolve(mockEnvelope(BACKTEST_STATISTICS));
      if (url.includes("/backtests"))
        return Promise.resolve(mockEnvelope(BACKTEST_LIST));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/backtests/index");
    render(
      <AppProviders>
        <mod.BacktestsListPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("MA均线回测")).toBeInTheDocument();
    });

    const table = screen.getByRole("table");
    expect(within(table).getByText("RSI回测")).toBeInTheDocument();
    expect(within(table).getByText("已完成")).toBeInTheDocument();
    expect(within(table).getByText("运行中")).toBeInTheDocument();
    expect(within(table).getByText("失败")).toBeInTheDocument();
  });

  it("given_completed_backtests_when_select_two_and_compare_then_correct_taskIds_sent", async () => {
    const compareCalls: string[] = [];
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/backtests/statistics"))
        return Promise.resolve(mockEnvelope(BACKTEST_STATISTICS));
      if (url.includes("/backtests/compare") && opts?.method === "POST") {
        const body = JSON.parse(opts?.body as string);
        compareCalls.push(JSON.stringify(body));
        return Promise.resolve(
          mockEnvelope({
            taskIds: body.taskIds,
            metrics: [
              { returnRate: 0.15, maxDrawdown: 0.08 },
              { returnRate: -0.05, maxDrawdown: 0.12 },
            ],
          }),
        );
      }
      if (url.includes("/backtests"))
        return Promise.resolve(mockEnvelope(BACKTEST_LIST));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/backtests/index");
    render(
      <AppProviders>
        <mod.BacktestsListPage />
      </AppProviders>,
    );

    // 等待列表渲染
    await waitFor(() => {
      expect(screen.getByText("MA均线回测")).toBeInTheDocument();
    });

    // 选择两个回测（通过 checkbox）
    const checkboxes = screen.getAllByRole("button", { name: /选择|取消选择/ });
    expect(checkboxes.length).toBeGreaterThanOrEqual(2);

    await user.click(checkboxes[0]); // bt-1
    await user.click(checkboxes[2]); // bt-3

    // 点击对比
    const compareBtn = screen.getByRole("button", { name: /对比选中/ });
    await user.click(compareBtn);

    // 验证发送的 taskIds
    await waitFor(() => {
      expect(compareCalls.length).toBe(1);
    });
    const sentBody = JSON.parse(compareCalls[0]);
    expect(sentBody.taskIds).toHaveLength(2);
    expect(sentBody.taskIds).toContain("bt-1");
    expect(sentBody.taskIds).toContain("bt-3");
  });

  it("given_less_than_two_selected_when_compare_then_shows_warning", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/backtests/statistics"))
        return Promise.resolve(mockEnvelope(BACKTEST_STATISTICS));
      if (url.includes("/backtests"))
        return Promise.resolve(mockEnvelope(BACKTEST_LIST));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/backtests/index");
    render(
      <AppProviders>
        <mod.BacktestsListPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("MA均线回测")).toBeInTheDocument();
    });

    // 只选择一个
    const checkboxes = screen.getAllByRole("button", { name: /选择|取消选择/ });
    await user.click(checkboxes[0]);

    // 对比按钮应被 disabled
    const compareBtn = screen.getByRole("button", { name: /对比选中/ });
    expect(compareBtn).toBeDisabled();
  });
});

describe("/backtests/$id (详情页)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("given_running_backtest_when_result_not_ready_then_shows_refresh_prompt", async () => {
    const runningTask = {
      id: "bt-running",
      userId: "u-1",
      strategyId: "s-1",
      status: "running",
      config: { startDate: "2025-01-01" },
      metrics: {},
      displayName: "运行中回测",
      createdAt: "2026-01-10T10:00:00Z",
      updatedAt: "2026-01-10T10:05:00Z",
    };

    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/result"))
        return Promise.resolve(
          mockErrorResponse(
            "BACKTEST_RESULT_NOT_READY",
            "backtest result is not ready",
          ),
        );
      if (url.includes("/related")) return Promise.resolve(mockEnvelope([]));
      if (url.includes("/backtests/"))
        return Promise.resolve(mockEnvelope(runningTask));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    // 需要 mock Route.useParams
    vi.mock("@tanstack/react-router", async () => {
      const actual = await vi.importActual<
        typeof import("@tanstack/react-router")
      >("@tanstack/react-router");
      return {
        ...actual,
        useNavigate: () => vi.fn(),
      };
    });

    const mod = await import("../../../app/routes/backtests/$id");

    // 手动 mock useParams — 需要 patch Route 对象
    const originalUseParams = mod.Route.useParams;
    mod.Route.useParams = (() => ({
      id: "bt-running",
    })) as typeof originalUseParams;

    render(
      <AppProviders>
        <mod.BacktestDetailPage />
      </AppProviders>,
    );

    // 等待页面渲染
    await waitFor(() => {
      expect(screen.getByText("运行中回测")).toBeInTheDocument();
    });

    // 结果面板应展示"运行中"提示 + 刷新按钮
    expect(screen.getByText("回测运行中")).toBeInTheDocument();
    expect(screen.getByText(/结果生成中/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "刷新结果" }),
    ).toBeInTheDocument();

    // 恢复
    mod.Route.useParams = originalUseParams;
  });

  it("given_completed_backtest_when_result_loaded_then_shows_metrics_cards", async () => {
    const completedTask = {
      id: "bt-done",
      userId: "u-1",
      strategyId: "s-1",
      status: "completed",
      config: {},
      metrics: {
        returnRate: 0.15,
        maxDrawdown: 0.08,
        sharpeRatio: 1.5,
        tradeCount: 42,
        winRate: 0.65,
      },
      displayName: "完成的回测",
      createdAt: "2026-01-10T10:00:00Z",
      updatedAt: "2026-01-10T12:00:00Z",
    };

    const resultData = {
      metrics: {
        returnRate: 0.15,
        maxDrawdown: 0.08,
        sharpeRatio: 1.5,
        tradeCount: 42,
        winRate: 0.65,
      },
      equityCurve: [],
      trades: [],
    };

    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (url.includes("/result"))
        return Promise.resolve(mockEnvelope(resultData));
      if (url.includes("/related")) return Promise.resolve(mockEnvelope([]));
      if (url.includes("/backtests/"))
        return Promise.resolve(mockEnvelope(completedTask));
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/backtests/$id");
    const originalUseParams = mod.Route.useParams;
    mod.Route.useParams = (() => ({
      id: "bt-done",
    })) as typeof originalUseParams;

    render(
      <AppProviders>
        <mod.BacktestDetailPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("完成的回测")).toBeInTheDocument();
    });

    // 验证指标卡片呈现
    expect(screen.getByText("收益率")).toBeInTheDocument();
    expect(screen.getByText("最大回撤")).toBeInTheDocument();
    expect(screen.getByText("夏普比率")).toBeInTheDocument();
    expect(screen.getByText("交易次数")).toBeInTheDocument();
    expect(screen.getByText("胜率")).toBeInTheDocument();

    // 数值格式正确
    expect(screen.getByText("15.00%")).toBeInTheDocument();
    expect(screen.getByText("8.00%")).toBeInTheDocument();
    expect(screen.getByText("1.50")).toBeInTheDocument();

    mod.Route.useParams = originalUseParams;
  });
});
