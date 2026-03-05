/**
 * UI Design System — TextField.test.tsx
 *
 * GIVEN: TextField 组件
 * WHEN:  渲染带 label / error / help / disabled 状态
 * THEN:  可访问性属性正确、error 状态渲染正确
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TextField } from "@qp/ui/TextField";

describe("TextField", () => {
  describe("label_and_input", () => {
    it("given_label_when_rendered_then_input_linked_to_label", () => {
      render(<TextField label="邮箱" />);
      const input = screen.getByLabelText("邮箱");
      expect(input).toBeInTheDocument();
      expect(input.tagName).toBe("INPUT");
    });
  });

  describe("error_state", () => {
    it("given_error_when_rendered_then_shows_error_message", () => {
      render(<TextField label="密码" error="密码不能为空" />);
      expect(screen.getByRole("alert")).toHaveTextContent("密码不能为空");
    });

    it("given_error_when_rendered_then_aria_invalid_true", () => {
      render(<TextField label="密码" error="必填" />);
      expect(screen.getByLabelText("密码")).toHaveAttribute(
        "aria-invalid",
        "true",
      );
    });

    it("given_error_when_rendered_then_input_describes_error", () => {
      render(<TextField label="密码" error="必填" id="pwd" />);
      const input = screen.getByLabelText("密码");
      expect(input).toHaveAttribute("aria-describedby", "pwd-error");
    });
  });

  describe("help_text", () => {
    it("given_help_when_rendered_then_shows_help_text", () => {
      render(<TextField label="用户名" help="3-20个字符" />);
      expect(screen.getByText("3-20个字符")).toBeInTheDocument();
    });

    it("given_help_and_error_when_rendered_then_shows_error_only", () => {
      render(<TextField label="用户名" help="3-20个字符" error="已被占用" />);
      expect(screen.getByRole("alert")).toHaveTextContent("已被占用");
      expect(screen.queryByText("3-20个字符")).not.toBeInTheDocument();
    });
  });

  describe("disabled_state", () => {
    it("given_disabled_when_rendered_then_input_is_disabled", () => {
      render(<TextField label="只读" disabled />);
      expect(screen.getByLabelText("只读")).toBeDisabled();
    });
  });

  describe("keyboard_accessibility", () => {
    it("given_input_when_tab_then_focusable", async () => {
      const user = userEvent.setup();
      render(<TextField label="名称" />);
      await user.tab();
      expect(screen.getByLabelText("名称")).toHaveFocus();
    });
  });
});
