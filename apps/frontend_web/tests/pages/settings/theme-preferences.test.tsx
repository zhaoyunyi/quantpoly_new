/**
 * ThemePreferencesForm — 主题模式可用项
 *
 * 目标：
 * - 仅展示可持久化的主题模式，避免出现不可持久化的 auto 选项
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThemePreferencesForm } from "../../../app/widgets/settings/ThemePreferencesForm";

const basePreferences = {
  version: 1,
  theme: {
    primaryColor: "#1677ff",
    darkMode: false,
  },
} as Record<string, unknown>;

describe("ThemePreferencesForm", () => {
  it("given_theme_mode_options_then_does_not_render_auto_mode", () => {
    render(
      <ThemePreferencesForm
        preferences={basePreferences}
        onPatch={vi.fn(async () => undefined)}
        saving={false}
      />,
    );

    expect(screen.getByText("浅色模式")).toBeInTheDocument();
    expect(screen.getAllByText("深色模式").length).toBeGreaterThan(0);
    expect(screen.queryByText("跟随系统")).not.toBeInTheDocument();
  });
});
