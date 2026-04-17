import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OrderConfirmDialog } from "../../../app/widgets/trading/OrderConfirmDialog";

function Wrapper({ children }: { children: React.ReactNode }) {
  return <div id="root">{children}</div>;
}

const baseProps = {
  open: true,
  onOpenChange: vi.fn(),
  side: "BUY" as const,
  symbol: "AAPL",
  quantity: 1000,
  price: 150.5,
  onConfirm: vi.fn(),
};

describe("OrderConfirmDialog", () => {
  it("given_open_dialog_when_rendered_then_shows_order_summary", async () => {
    render(
      <Wrapper>
        <OrderConfirmDialog {...baseProps} />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("1,000")).toBeInTheDocument();
    expect(screen.getByText("¥150.50")).toBeInTheDocument();
    expect(screen.getByText("¥150,500.00")).toBeInTheDocument();
  });

  it("given_buy_order_when_rendered_then_shows_buy_direction", async () => {
    render(
      <Wrapper>
        <OrderConfirmDialog {...baseProps} side="BUY" />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("买入")).toBeInTheDocument();
    });
  });

  it("given_sell_order_when_rendered_then_shows_sell_direction", async () => {
    render(
      <Wrapper>
        <OrderConfirmDialog {...baseProps} side="SELL" />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("卖出")).toBeInTheDocument();
    });
  });

  it("given_confirm_button_when_clicked_then_calls_onConfirm", async () => {
    const onConfirm = vi.fn();
    render(
      <Wrapper>
        <OrderConfirmDialog {...baseProps} onConfirm={onConfirm} />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: "确认下单" });
    await userEvent.click(confirmBtn);

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("given_cancel_button_when_clicked_then_calls_onOpenChange_false", async () => {
    const onOpenChange = vi.fn();
    render(
      <Wrapper>
        <OrderConfirmDialog {...baseProps} onOpenChange={onOpenChange} />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("取消")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("取消"));

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
