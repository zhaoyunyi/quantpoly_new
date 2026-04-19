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
    Link: ({ children, to, ...props }: Record<string, unknown>) => (
      <a href={String(to ?? "")} {...(props as Record<string, unknown>)}>
        {children as any}
      </a>
    ),
    useNavigate: () => vi.fn(),
  };
});

function mockEnvelope<T>(data: T) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve({ success: true, message: "ok", data }),
  };
}

function mockPagedEnvelope<T>(items: T[], total: number) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () =>
      Promise.resolve({
        success: true,
        message: "ok",
        data: { items, total, page: 1, pageSize: 10 },
      }),
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

const templates = [
  {
    templateId: "moving_average",
    name: "双均线",
    requiredParameters: {
      shortWindow: { type: "int", min: 2, max: 200 },
      longWindow: { type: "int", min: 3, max: 400 },
    },
    defaults: { shortWindow: 5, longWindow: 20 },
  },
  {
    templateId: "mean_reversion",
    name: "均值回归",
    requiredParameters: {
      window: { type: "int", min: 2, max: 300 },
      entryZ: { type: "float", min: 0.1, max: 5.0 },
      exitZ: { type: "float", min: 0.0, max: 5.0 },
    },
    defaults: { window: 20, entryZ: 1.5, exitZ: 0.5 },
  },
  {
    templateId: "macd",
    name: "MACD 趋势",
    requiredParameters: {
      fast: { type: "int", min: 1, max: 100 },
      slow: { type: "int", min: 2, max: 200 },
      signal: { type: "int", min: 1, max: 100 },
    },
    defaults: { fast: 12, slow: 26, signal: 9 },
  },
];

const reports = [
  {
    reportId: "failed-12345678",
    status: "failed",
    error: "no market data available",
    createdAt: "2026-01-01T00:00:00Z",
  },
  {
    reportId: "completed-12345678",
    status: "completed",
    overallScore: 82,
    overfitRisk: "LOW",
    inSampleReturn: 0.12,
    outSampleReturn: 0.08,
    returnRatio: 0.67,
    paramSensitivity: {},
    tradeCount: 12,
    maxDrawdown: 0.14,
    sharpeRatio: 1.23,
    warnings: [],
    createdAt: "2026-01-02T00:00:00Z",
  },
];

describe("/strategies/health", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("filters unsupported templates and safely renders failed history items", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me")) {
        return Promise.resolve(mockEnvelope(meData));
      }
      if (url.includes("/strategies/templates")) {
        return Promise.resolve(mockEnvelope(templates));
      }
      if (url.includes("/strategy-health")) {
        return Promise.resolve(mockPagedEnvelope(reports, reports.length));
      }
      throw new Error(`unexpected: ${url}`);
    });
    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/strategies/health");
    const user = userEvent.setup();

    render(
      <AppProviders>
        <mod.StrategyHealthPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "策略健康报告" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("failed-1")).toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(2);

    const templateTrigger = screen.getByLabelText("策略模板");
    await user.click(templateTrigger);

    const optionList = await screen.findByRole("listbox");
    expect(within(optionList).getByText("双均线")).toBeInTheDocument();
    expect(within(optionList).getByText("均值回归")).toBeInTheDocument();
    expect(within(optionList).queryByText("MACD 趋势")).not.toBeInTheDocument();

    await user.click(screen.getByText("failed-1"));

    await waitFor(() => {
      expect(screen.getByText("报告执行失败")).toBeInTheDocument();
      expect(screen.getByText("no market data available")).toBeInTheDocument();
    });
  });
});
