import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthProvider, configureClient } from "@qp/api-client";
import { ThemeProvider } from "@qp/ui";
import { AppShell } from "@qp/shell";

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
  };
});

const AUTH_USER = {
  id: "u-1",
  email: "user@example.com",
  displayName: "测试用户",
  isActive: true,
  emailVerified: true,
  role: "user",
  level: 1,
};

function mockEnvelope<T>(data: T) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: () => Promise.resolve({ success: true, message: "ok", data }),
  };
}

describe("AppShell theme toggle", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    configureClient({ baseUrl: "http://localhost:8000" });

    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: true,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("given_system_theme_resolved_dark_when_toggled_then_switches_to_light", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(mockEnvelope({ status: "ok" }))));

    const user = userEvent.setup();

    render(
      <ThemeProvider defaultTheme="system">
        <AuthProvider initialUser={AUTH_USER} initialResolved>
          <AppShell>
            <div>shell-content</div>
          </AppShell>
        </AuthProvider>
      </ThemeProvider>,
    );

    expect(document.documentElement.classList.contains("dark")).toBe(true);

    const toggle = screen.getByRole("button", { name: "切换到浅色模式" });
    await user.click(toggle);

    await waitFor(() => {
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });
    expect(screen.getByRole("button", { name: "切换到深色模式" })).toBeInTheDocument();
    expect(localStorage.getItem("qp-theme")).toBe("light");
  });
});
