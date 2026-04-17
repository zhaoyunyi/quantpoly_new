/**
 * ThemePreferencesForm — 主题模式可用项
 *
 * 目标：
 * - 仅展示可持久化的主题模式，避免出现不可持久化的 auto 选项
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "@qp/ui";
import { ThemePreferencesForm } from "../../../app/widgets/settings/ThemePreferencesForm";

const basePreferences = {
  version: 1,
  theme: {
    mode: "system",
    primaryColor: "primary-700",
  },
} as Record<string, unknown>;

describe("ThemePreferencesForm", () => {
  it("given_theme_mode_options_when_rendered_then_shows_light_dark_and_system", () => {
    render(
      <ThemeProvider>
        <ThemePreferencesForm
          preferences={basePreferences}
          onPatch={vi.fn(async () => undefined)}
          saving={false}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText("浅色模式")).toBeInTheDocument();
    expect(screen.getAllByText("深色模式").length).toBeGreaterThan(0);
    expect(screen.getByText("跟随系统")).toBeInTheDocument();
    expect(screen.queryByText("自动模式")).not.toBeInTheDocument();
  });

  it("given_unsaved_primary_color_when_mode_changed_then_does_not_persist_color", async () => {
    const onPatch = vi.fn(async () => undefined);
    const user = userEvent.setup();

    render(
      <ThemeProvider defaultTheme="system">
        <ThemePreferencesForm
          preferences={basePreferences}
          onPatch={onPatch}
          saving={false}
        />
      </ThemeProvider>,
    );

    await user.click(screen.getByRole("button", { name: "天蓝" }));
    await user.click(screen.getByRole("button", { name: "深色模式" }));

    expect(onPatch).toHaveBeenCalledTimes(1);
    expect(onPatch).toHaveBeenCalledWith({ theme: { mode: "dark" } });
    expect(screen.getByText("主色调有未保存的更改")).toBeInTheDocument();
  });

  it("given_saved_theme_mode_when_rendered_then_uses_saved_mode_as_current_selection", () => {
    localStorage.setItem("qp-theme", "light");

    render(
      <ThemeProvider defaultTheme="light">
        <ThemePreferencesForm
          preferences={{
            version: 1,
            theme: {
              mode: "dark",
              darkMode: true,
              primaryColor: "primary-700",
            },
          }}
          onPatch={vi.fn(async () => undefined)}
          saving={false}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText("dark")).toBeInTheDocument();
  });
});
