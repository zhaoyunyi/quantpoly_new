import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
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

const { exportCsvMock } = vi.hoisted(() => ({
  exportCsvMock: vi.fn(),
}));

vi.mock("../../../app/shared/exportCsv", () => ({
  exportCsv: exportCsvMock,
}));

function mockEnvelope<T>(data: T) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve({ success: true, message: "ok", data }),
  };
}

const ME_RESPONSE = {
  id: "u-1",
  email: "u1@example.com",
  displayName: "U1",
  isActive: true,
  emailVerified: true,
  role: "user",
  level: 1,
};

const STRATEGIES = [
  {
    id: "s-1",
    name: "Alpha",
    template: "tpl-a",
    status: "active",
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-02T00:00:00Z",
  },
  {
    id: "s-2",
    name: "Beta",
    template: "tpl-b",
    status: "active",
    createdAt: "2026-01-03T00:00:00Z",
    updatedAt: "2026-01-04T00:00:00Z",
  },
];

describe("/strategies/compare", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    exportCsvMock.mockReset();
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_localized_metrics_when_export_csv_then_uses_shared_csv_escaping", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/users/me")) {
        return Promise.resolve(mockEnvelope(ME_RESPONSE));
      }
      if (url.includes("/strategies?")) {
        return Promise.resolve(
          mockEnvelope({ items: STRATEGIES, total: 2, page: 1, pageSize: 200 }),
        );
      }
      if (url.includes("/strategies/s-1/backtests")) {
        return Promise.resolve(mockEnvelope({ items: [{ id: "bt-1" }] }));
      }
      if (url.includes("/strategies/s-2/backtests")) {
        return Promise.resolve(mockEnvelope({ items: [{ id: "bt-2" }] }));
      }
      if (url.includes("/backtests/compare")) {
        return Promise.resolve(
          mockEnvelope({
            metrics: [{ totalReturn: 1234.5 }, { totalReturn: 9876.5 }],
          }),
        );
      }
      return Promise.resolve(mockEnvelope({}));
    });
    vi.stubGlobal("fetch", mockFetch);

    const user = userEvent.setup();
    const mod = await import("../../../app/routes/strategies/compare");

    render(
      <AppProviders>
        <mod.StrategyComparePage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("Alpha")).toBeInTheDocument();
      expect(screen.getByText("Beta")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Alpha/ }));
    await user.click(screen.getByRole("button", { name: /Beta/ }));
    await user.click(screen.getByRole("button", { name: "开始对比" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "导出 CSV" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "导出 CSV" }));

    expect(exportCsvMock).toHaveBeenCalledTimes(1);
    expect(exportCsvMock).toHaveBeenCalledWith(
      "strategy-compare.csv",
      ["指标", "Alpha", "Beta"],
      [["totalReturn", "1,234.5", "9,876.5"]],
    );
  });
});
