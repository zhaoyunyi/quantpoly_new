/**
 * UI Design System — Toast.test.tsx
 *
 * GIVEN: Toast 通知系统
 * WHEN:  调用 show / dismiss
 * THEN:  渲染和关闭通知
 */

import { describe, it, expect } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToastProvider, useToast } from "@qp/ui/Toast";

function TestComponent() {
  const toast = useToast();
  return (
    <button onClick={() => toast.show("操作成功", "success")}>触发</button>
  );
}

describe("Toast", () => {
  it("given_provider_when_show_called_then_renders_toast", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>,
    );

    await user.click(screen.getByText("触发"));
    expect(screen.getByText("操作成功")).toBeInTheDocument();
  });

  it("given_toast_when_close_clicked_then_dismisses", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>,
    );

    await user.click(screen.getByText("触发"));
    expect(screen.getByText("操作成功")).toBeInTheDocument();

    await user.click(screen.getByLabelText("关闭通知"));
    expect(screen.queryByText("操作成功")).not.toBeInTheDocument();
  });
});
