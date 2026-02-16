/**
 * /settings/account — 失败交互回归
 *
 * 目标：
 * - 改密失败时不清空输入
 * - 注销失败时对话框保持打开且确认文本保留
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppProviders, bootstrapApiClient } from "../../../app/entry_wiring";

const { mockNavigate } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
}));

vi.mock("@qp/shell/redirect", () => ({
  redirectTo: vi.fn(),
}));

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-router")>(
    "@tanstack/react-router",
  );
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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

function failureEnvelope(message: string) {
  return {
    success: false,
    error: {
      code: "BAD_REQUEST",
      message,
    },
  };
}

describe("/settings/account — 失败场景", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    bootstrapApiClient("http://localhost:8000");
    mockNavigate.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_change_password_fails_when_submit_then_keeps_inputs", async () => {
    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/users/me") && (!init || !init.method || init.method === "GET")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(ME_RESPONSE),
        });
      }

      if (url.endsWith("/users/me/password") && init?.method === "PATCH") {
        return Promise.resolve({
          ok: false,
          status: 422,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(failureEnvelope("当前密码错误")),
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, message: "ok", data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/settings/account");

    render(
      <AppProviders>
        <mod.AccountPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: "账户安全" }),
      ).toBeInTheDocument();
    });

    const currentPwd = screen.getByLabelText("当前密码") as HTMLInputElement;
    const newPwd = screen.getByLabelText("新密码") as HTMLInputElement;
    const confirmPwd = screen.getByLabelText("确认新密码") as HTMLInputElement;
    await userEvent.type(currentPwd, "old-password");
    await userEvent.type(newPwd, "new-password");
    await userEvent.type(confirmPwd, "new-password");

    await userEvent.click(screen.getByRole("button", { name: "修改密码" }));

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, i]) =>
            String(u).endsWith("/users/me/password") &&
            (i as RequestInit)?.method === "PATCH",
        ),
      ).toBe(true);
    });

    expect(currentPwd.value).toBe("old-password");
    expect(newPwd.value).toBe("new-password");
    expect(confirmPwd.value).toBe("new-password");
  });

  it("given_delete_fails_when_confirm_then_keeps_dialog_open_and_text", async () => {
    const mockFetch = vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/users/me") && (!init || !init.method || init.method === "GET")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(ME_RESPONSE),
        });
      }

      if (url.endsWith("/users/me") && init?.method === "DELETE") {
        return Promise.resolve({
          ok: false,
          status: 422,
          headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve(failureEnvelope("注销失败")),
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: () => Promise.resolve({ success: true, message: "ok", data: {} }),
      });
    });

    vi.stubGlobal("fetch", mockFetch);

    const mod = await import("../../../app/routes/settings/account");

    render(
      <AppProviders>
        <mod.AccountPage />
      </AppProviders>,
    );

    await waitFor(() => {
      expect(screen.getByText("注销我的账户")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("注销我的账户"));
    await waitFor(() => {
      expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("请输入 DELETE") as HTMLInputElement;
    await userEvent.type(input, "DELETE");
    await userEvent.click(screen.getByText("确认注销"));

    await waitFor(() => {
      expect(
        mockFetch.mock.calls.some(
          ([u, i]) =>
            String(u).endsWith("/users/me") &&
            (i as RequestInit)?.method === "DELETE",
        ),
      ).toBe(true);
    });

    expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    expect((screen.getByPlaceholderText("请输入 DELETE") as HTMLInputElement).value).toBe(
      "DELETE",
    );
  });
});
