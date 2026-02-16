/**
 * DangerZone / 注销确认对话框 — 单元测试
 *
 * 目标：
 * - 注销确认对话框默认禁用确认按钮
 * - 输入错误文本时保持禁用
 * - 输入正确确认文本后启用确认按钮
 * - 确认后调用 onDeleteAccount
 */

import type { ComponentProps } from "react";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DangerZone } from "../../../app/widgets/settings/DangerZone";

// Dialog 需要 portal container
function Wrapper({ children }: { children: React.ReactNode }) {
  return <div id="root">{children}</div>;
}

describe("DangerZone — 注销确认逻辑", () => {
  type DangerZoneProps = ComponentProps<typeof DangerZone>;
  type OnDeleteAccount = DangerZoneProps["onDeleteAccount"];
  type OnChangePassword = DangerZoneProps["onChangePassword"];

  let onDeleteAccount: OnDeleteAccount;
  let onChangePassword: OnChangePassword;
  let onDeleteAccountMock: Mock<OnDeleteAccount>;
  let onChangePasswordMock: Mock<OnChangePassword>;

  beforeEach(() => {
    onDeleteAccountMock = vi.fn<OnDeleteAccount>().mockResolvedValue(undefined);
    onChangePasswordMock = vi
      .fn<OnChangePassword>()
      .mockResolvedValue(undefined);
    onDeleteAccount = onDeleteAccountMock;
    onChangePassword = onChangePasswordMock;
  });

  it("given_dialog_closed_when_click_delete_button_then_opens_dialog", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    const triggerBtn = screen.getByText("注销我的账户");
    await userEvent.click(triggerBtn);

    await waitFor(() => {
      expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    });
  });

  it("given_dialog_open_when_no_input_then_confirm_button_disabled", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    await userEvent.click(screen.getByText("注销我的账户"));

    await waitFor(() => {
      expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    });

    const confirmBtn = screen.getByText("确认注销");
    expect(confirmBtn).toBeDisabled();
  });

  it("given_dialog_open_when_wrong_text_then_confirm_still_disabled", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    await userEvent.click(screen.getByText("注销我的账户"));

    await waitFor(() => {
      expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("请输入 DELETE");
    await userEvent.type(input, "WRONG");

    const confirmBtn = screen.getByText("确认注销");
    expect(confirmBtn).toBeDisabled();
  });

  it("given_dialog_open_when_type_DELETE_then_confirm_enabled_and_calls_handler", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    await userEvent.click(screen.getByText("注销我的账户"));

    await waitFor(() => {
      expect(screen.getByText("确认注销账户")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("请输入 DELETE");
    await userEvent.type(input, "DELETE");

    const confirmBtn = screen.getByText("确认注销");
    expect(confirmBtn).not.toBeDisabled();

    await userEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onDeleteAccountMock).toHaveBeenCalledTimes(1);
    });
  });

  it("given_password_form_when_passwords_mismatch_then_shows_error", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    const currentPwd = screen.getByLabelText("当前密码");
    const newPwd = screen.getByLabelText("新密码");
    const confirmPwd = screen.getByLabelText("确认新密码");

    await userEvent.type(currentPwd, "old123");
    await userEvent.type(newPwd, "newpassword");
    await userEvent.type(confirmPwd, "different");

    const changePwdBtn = screen.getByRole("button", { name: "修改密码" });
    await userEvent.click(changePwdBtn);

    await waitFor(() => {
      expect(screen.getByText("两次输入的密码不一致")).toBeInTheDocument();
    });

    expect(onChangePasswordMock).not.toHaveBeenCalled();
  });

  it("given_password_form_when_valid_then_calls_handler", async () => {
    render(
      <Wrapper>
        <DangerZone
          onChangePassword={onChangePassword}
          onDeleteAccount={onDeleteAccount}
          changingPassword={false}
          deletingAccount={false}
        />
      </Wrapper>,
    );

    const currentPwd = screen.getByLabelText("当前密码");
    const newPwd = screen.getByLabelText("新密码");
    const confirmPwd = screen.getByLabelText("确认新密码");

    await userEvent.type(currentPwd, "old123456");
    await userEvent.type(newPwd, "newpassword");
    await userEvent.type(confirmPwd, "newpassword");

    const changePwdBtn = screen.getByRole("button", { name: "修改密码" });
    await userEvent.click(changePwdBtn);

    await waitFor(() => {
      expect(onChangePasswordMock).toHaveBeenCalledWith({
        currentPassword: "old123456",
        newPassword: "newpassword",
        revokeAllSessions: false,
      });
    });
  });
});
