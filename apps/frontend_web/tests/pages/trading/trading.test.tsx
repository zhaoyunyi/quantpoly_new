/**
 * Trading Pages Tests
 *
 * 覆盖：
 * 5.1 buy/sell 冲突错误码映射与提示
 * 5.2 risk assessment pending 分支
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppProviders, bootstrapApiClient } from "../../../app/entry_wiring";
import { ToastProvider } from "@qp/ui";
import { OrderTicket } from "../../../app/widgets/trading/OrderTicket";

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

const ACCOUNTS = [
  {
    id: "acc-1",
    userId: "u-1",
    accountName: "主账户",
    isActive: true,
    createdAt: "2026-01-01T00:00:00Z",
  },
];

const OVERVIEW = {
  positionCount: 2,
  totalMarketValue: 50000,
  unrealizedPnl: 1500,
  tradeCount: 10,
  turnover: 100000,
  orderCount: 3,
  pendingOrderCount: 1,
  filledOrderCount: 2,
  cancelledOrderCount: 0,
  failedOrderCount: 0,
  cashBalance: 80000,
};

const POSITIONS = [
  {
    id: "p-1",
    userId: "u-1",
    accountId: "acc-1",
    symbol: "AAPL",
    quantity: 100,
    avgPrice: 150,
    lastPrice: 160,
  },
];

const ORDERS = [
  {
    id: "ord-1",
    userId: "u-1",
    accountId: "acc-1",
    symbol: "AAPL",
    side: "BUY",
    quantity: 50,
    price: 155,
    status: "filled",
    createdAt: "2026-01-10T00:00:00Z",
    updatedAt: "2026-01-10T00:00:00Z",
  },
];

describe("OrderTicket (下单表单)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_insufficient_funds_when_submit_buy_then_shows_mapped_error", async () => {
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (
        url.includes("/trading/accounts/acc-1/buy") &&
        opts?.method === "POST"
      ) {
        return Promise.resolve(mockError("INSUFFICIENT_FUNDS", "可用资金不足"));
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    render(
      <ToastProvider>
        <OrderTicket accountId="acc-1" />
      </ToastProvider>,
    );

    await user.type(screen.getByLabelText("标的代码"), "AAPL");
    await user.type(screen.getByLabelText("数量"), "10");
    await user.type(screen.getByLabelText("价格"), "100");

    await user.click(screen.getByRole("button", { name: "确认买入" }));

    expect(
      await screen.findByText("可用资金不足，无法完成买入。请存入资金后重试。"),
    ).toBeInTheDocument();
  });

  it("given_insufficient_position_when_submit_sell_then_shows_mapped_error", async () => {
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (
        url.includes("/trading/accounts/acc-1/sell") &&
        opts?.method === "POST"
      ) {
        return Promise.resolve(
          mockError("INSUFFICIENT_POSITION", "可用持仓不足"),
        );
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    render(
      <ToastProvider>
        <OrderTicket accountId="acc-1" />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "卖出" }));
    await user.type(screen.getByLabelText("标的代码"), "AAPL");
    await user.type(screen.getByLabelText("数量"), "10");
    await user.type(screen.getByLabelText("价格"), "100");

    await user.click(screen.getByRole("button", { name: "确认卖出" }));

    expect(
      await screen.findByText("可用持仓不足，无法完成卖出。请确认持仓数量。"),
    ).toBeInTheDocument();
  });
});

describe("/trading/analytics (分析报表)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_risk_assessment_pending_when_render_then_shows_pending_banner", async () => {
    const mockFetch = vi.fn((url: string, opts?: RequestInit) => {
      if (url.endsWith("/users/me"))
        return Promise.resolve(mockEnvelope(meData));
      if (
        url.endsWith("/trading/accounts") &&
        (!opts || !opts.method || opts.method === "GET")
      ) {
        return Promise.resolve(mockEnvelope(ACCOUNTS));
      }
      if (url.includes("/risk-metrics")) {
        return Promise.resolve(
          mockEnvelope({
            accountId: "acc-1",
            riskScore: 45,
            riskLevel: "medium",
            exposureRatio: 0.6,
            leverage: 1.2,
            unrealizedPnl: 1500,
            pendingOrderCount: 1,
            evaluatedAt: "2026-01-10T00:00:00Z",
          }),
        );
      }
      if (url.includes("/equity-curve"))
        return Promise.resolve(mockEnvelope([]));
      if (url.includes("/trade-stats")) {
        return Promise.resolve(
          mockEnvelope({ tradeCount: 10, turnover: 100000 }),
        );
      }
      if (url.includes("/cash-flows/summary")) {
        return Promise.resolve(
          mockEnvelope({
            flowCount: 5,
            totalInflow: 100000,
            totalOutflow: -20000,
            netFlow: 80000,
            latestFlowAt: "2026-01-10T00:00:00Z",
          }),
        );
      }
      if (url.includes("/cash-flows")) return Promise.resolve(mockEnvelope([]));
      // risk-assessment GET 返回 202 PENDING
      if (
        url.includes("/risk-assessment") &&
        (!opts || !opts.method || opts.method === "GET")
      ) {
        return Promise.resolve(
          mockError("RISK_ASSESSMENT_PENDING", "评估正在生成中", 202),
        );
      }
      // risk-assessment evaluate POST 也返回 PENDING
      if (
        url.includes("/risk-assessment/evaluate") &&
        opts?.method === "POST"
      ) {
        return Promise.resolve(
          mockError("RISK_ASSESSMENT_PENDING", "评估正在生成中", 202),
        );
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/trading/analytics");
    render(
      <AppProviders>
        <mod.TradingAnalyticsPage />
      </AppProviders>,
    );

    // 验证页面标题渲染
    await waitFor(() => {
      expect(screen.getByText("分析报表")).toBeInTheDocument();
    });

    // 等待账户选择器就绪
    const user = userEvent.setup();
    await user.click(await screen.findByText("选择账户"));
    await user.click(await screen.findByText("主账户"));

    expect(
      await screen.findByText("风险评估快照正在生成中，请稍后刷新查看结果。"),
    ).toBeInTheDocument();
  });
});
