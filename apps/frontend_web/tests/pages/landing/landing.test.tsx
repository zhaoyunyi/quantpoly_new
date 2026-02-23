/**
 * Landing Page — /
 *
 * 验收场景（Given/When/Then）：
 * - 页面包含注册/登录 CTA
 * - 页面包含免责声明
 * - 后端可用时展示"服务运行中"
 * - 后端不可用时展示"服务暂不可用"（不阻断页面）
 * - 核心能力区域展示四大模块
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";

import { bootstrapApiClient } from "../../../app/entry_wiring";
import { LandingPage } from "../../../app/widgets/landing/LandingContent";

describe("/ (Landing Page)", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.restoreAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    bootstrapApiClient("http://localhost:8000");
  });

  afterEach(() => {
    try {
      const actWarnings = consoleErrorSpy.mock.calls.filter((call: unknown[]) =>
        call.some((arg: unknown) => String(arg).includes("not wrapped in act")),
      );
      expect(actWarnings).toHaveLength(0);
    } finally {
      consoleErrorSpy.mockRestore();
      vi.unstubAllGlobals();
      cleanup();
    }
  });

  it("given_landing_when_render_then_shows_cta_and_disclaimer", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () =>
            Promise.resolve({
              success: true,
              message: "ok",
              data: { status: "healthy", enabledContexts: ["user_auth"] },
            }),
        });
      }
      // 返回空响应以防其他请求
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const { container } = render(<LandingPage />);

    // CTA：注册入口
    expect(screen.getByText("免费注册")).toBeInTheDocument();
    expect(screen.getByText("立即开始")).toBeInTheDocument();

    // CTA：登录入口
    expect(screen.getByText("登录")).toBeInTheDocument();
    expect(screen.getByText("已有账号？登录")).toBeInTheDocument();

    // 免责声明（强制）
    const disclaimer = screen.getByTestId("disclaimer");
    expect(disclaimer).toBeInTheDocument();
    expect(disclaimer.textContent).toContain("不构成任何投资建议");
    expect(disclaimer.textContent).toContain("不代表未来表现");

    // CTA 不允许无效交互嵌套（a > button）
    expect(container.querySelector("a button")).toBeNull();
    await screen.findByText("服务运行中");
  });

  it("given_landing_when_render_then_shows_core_features", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () =>
          Promise.resolve({
            success: true,
            data: { status: "healthy", enabledContexts: [] },
          }),
      }),
    );

    vi.stubGlobal("fetch", mockFetch);

    render(<LandingPage />);

    // 四大核心能力模块
    expect(screen.getByText("策略管理")).toBeInTheDocument();
    expect(screen.getByText("回测引擎")).toBeInTheDocument();
    expect(screen.getByText("风控中心")).toBeInTheDocument();
    expect(screen.getByText("实时监控")).toBeInTheDocument();
    await screen.findByText("服务运行中");
  });

  it("given_health_ok_when_render_then_shows_service_running", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () =>
            Promise.resolve({
              success: true,
              message: "ok",
              data: { status: "healthy", enabledContexts: ["user_auth"] },
            }),
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

    const { container } = render(<LandingPage />);

    await waitFor(() => {
      expect(screen.getByTestId("health-ok")).toBeInTheDocument();
    });

    expect(screen.getByText("服务运行中")).toBeInTheDocument();
    expect(container.querySelector(".bg-state-down")).toBeNull();
  });

  it("given_health_fail_when_render_then_shows_unavailable_without_blocking", async () => {
    const mockFetch = vi.fn((url: string) => {
      if (url.endsWith("/health")) {
        return Promise.reject(new Error("Network error"));
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const { container } = render(<LandingPage />);

    // 页面不被阻断——CTA 仍可见
    expect(screen.getByText("免费注册")).toBeInTheDocument();
    expect(screen.getByText("登录")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("服务暂不可用")).toBeInTheDocument();
    });

    // 免责声明依然存在
    expect(screen.getByTestId("disclaimer")).toBeInTheDocument();
    expect(container.querySelector(".bg-state-risk")).toBeNull();
  });

  it("given_landing_when_render_then_has_value_proposition", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () =>
          Promise.resolve({
            success: true,
            data: { status: "healthy", enabledContexts: [] },
          }),
      }),
    );

    vi.stubGlobal("fetch", mockFetch);

    render(<LandingPage />);

    // Hero 一句话价值主张
    expect(screen.getByText("可解释的量化分析工具")).toBeInTheDocument();

    // 品牌标识
    expect(screen.getByText("QuantPoly")).toBeInTheDocument();

    // 风险提示
    expect(screen.getByText(/量化交易存在风险/)).toBeInTheDocument();
    await screen.findByText("服务运行中");
  });
});
