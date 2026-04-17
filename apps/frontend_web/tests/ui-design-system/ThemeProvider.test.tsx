import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThemeProvider } from "@qp/ui";

describe("ThemeProvider", () => {
  it("given_missing_match_media_when_rendered_then_falls_back_without_crashing", () => {
    vi.stubGlobal("window", window);
    vi.stubGlobal("document", document);
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: undefined,
    });

    render(
      <ThemeProvider>
        <div>theme-ready</div>
      </ThemeProvider>,
    );

    expect(screen.getByText("theme-ready")).toBeInTheDocument();
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
