/**
 * UI Design System — Button.test.tsx
 *
 * GIVEN: Button 组件
 * WHEN:  渲染不同变体 / 状态
 * THEN:  交互行为、可访问性、样式正确
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "@qp/ui/Button";

describe("Button", () => {
  describe("default_render", () => {
    it("given_default_props_when_rendered_then_shows_text", () => {
      render(<Button>提交</Button>);
      expect(screen.getByRole("button", { name: "提交" })).toBeInTheDocument();
    });

    it("given_default_props_when_rendered_then_type_is_button", () => {
      render(<Button>确定</Button>);
      expect(screen.getByRole("button")).toHaveAttribute("type", "button");
    });
  });

  describe("click_interaction", () => {
    it("given_enabled_button_when_clicked_then_fires_handler", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<Button onClick={onClick}>点击</Button>);
      await user.click(screen.getByRole("button"));
      expect(onClick).toHaveBeenCalledOnce();
    });

    it("given_disabled_button_when_clicked_then_no_handler", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(
        <Button onClick={onClick} disabled>
          禁用
        </Button>,
      );
      await user.click(screen.getByRole("button"));
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe("loading_state", () => {
    it("given_loading_when_rendered_then_aria_busy_true", () => {
      render(<Button loading>加载中</Button>);
      const btn = screen.getByRole("button");
      expect(btn).toHaveAttribute("aria-busy", "true");
      expect(btn).toBeDisabled();
    });
  });

  describe("keyboard_accessibility", () => {
    it("given_button_when_tab_then_focusable", async () => {
      const user = userEvent.setup();
      render(<Button>聚焦</Button>);
      await user.tab();
      expect(screen.getByRole("button")).toHaveFocus();
    });

    it("given_disabled_button_when_tab_then_not_focusable", async () => {
      const user = userEvent.setup();
      render(<Button disabled>禁用</Button>);
      await user.tab();
      expect(screen.getByRole("button")).not.toHaveFocus();
    });
  });

  describe("variants", () => {
    it("given_primary_variant_when_rendered_then_has_primary_class", () => {
      render(<Button variant="primary">主要</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("bg-primary-700");
    });

    it("given_secondary_variant_when_rendered_then_has_secondary_class", () => {
      render(<Button variant="secondary">次要</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("bg-bg-subtle");
    });

    it("given_ghost_variant_when_rendered_then_has_ghost_class", () => {
      render(<Button variant="ghost">文字</Button>);
      const btn = screen.getByRole("button");
      expect(btn.className).toContain("bg-transparent");
    });
  });
});
