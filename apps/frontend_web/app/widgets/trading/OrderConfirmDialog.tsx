import { Button, Dialog } from "@qp/ui";
import type { OrderSide } from "@qp/api-client";

export interface OrderConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  side: OrderSide;
  symbol: string;
  quantity: number;
  price: number;
  onConfirm: () => void;
  loading?: boolean;
}

const rows = (
  side: OrderSide,
  symbol: string,
  quantity: number,
  price: number,
) => [
  {
    label: "方向",
    value: (
      <span
        className={
          side === "BUY" ? "state-up font-medium" : "state-down font-medium"
        }
      >
        {side === "BUY" ? "买入" : "卖出"}
      </span>
    ),
  },
  { label: "标的", value: symbol },
  { label: "数量", value: quantity.toLocaleString("zh-CN") },
  {
    label: "价格",
    value: `¥${price.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  },
  {
    label: "预估金额",
    value: `¥${(quantity * price).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  },
];

export function OrderConfirmDialog({
  open,
  onOpenChange,
  side,
  symbol,
  quantity,
  price,
  onConfirm,
  loading,
}: OrderConfirmDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="确认下单"
      description="请确认以下订单信息，提交后将立即执行。"
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button variant="primary" onClick={onConfirm} loading={loading}>
            确认下单
          </Button>
        </>
      }
    >
      <div className="flex flex-col">
        {rows(side, symbol, quantity, price).map((row) => (
          <div
            key={row.label}
            className="flex justify-between py-xs border-b border-secondary-300/10 last:border-0"
          >
            <span className="text-body text-text-secondary">{row.label}</span>
            <span className="text-body font-medium">{row.value}</span>
          </div>
        ))}
      </div>
    </Dialog>
  );
}
