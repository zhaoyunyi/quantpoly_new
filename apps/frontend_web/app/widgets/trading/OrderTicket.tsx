/**
 * OrderTicket — 买入/卖出下单表单
 *
 * 支持 Buy/Sell 切换，字段：标的、数量、价格。
 * 处理 INSUFFICIENT_FUNDS / INSUFFICIENT_POSITION 错误码。
 */

import { useState, type ChangeEvent } from "react";

import { buy, sell } from "@qp/api-client";
import type { AppError, OrderSide } from "@qp/api-client";
import { Button, TextField, useToast } from "@qp/ui";

export interface OrderTicketProps {
  accountId: string;
  onSuccess?: () => void;
}

const ERROR_MAP: Record<string, string> = {
  INSUFFICIENT_FUNDS: "可用资金不足，无法完成买入。请存入资金后重试。",
  INSUFFICIENT_POSITION: "可用持仓不足，无法完成卖出。请确认持仓数量。",
};

export function OrderTicket({ accountId, onSuccess }: OrderTicketProps) {
  const toast = useToast();
  const [side, setSide] = useState<OrderSide>("BUY");
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const qty = parseFloat(quantity);
    const prc = parseFloat(price);
    if (
      !symbol.trim() ||
      Number.isNaN(qty) ||
      qty <= 0 ||
      Number.isNaN(prc) ||
      prc <= 0
    ) {
      setError("请填写完整的下单信息（标的、数量 > 0、价格 > 0）");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const fn = side === "BUY" ? buy : sell;
      await fn(accountId, { symbol: symbol.trim(), quantity: qty, price: prc });
      toast.show(side === "BUY" ? "买入成功" : "卖出成功", "success");
      setSymbol("");
      setQuantity("");
      setPrice("");
      onSuccess?.();
    } catch (err) {
      const appErr = err as AppError;
      const mapped = ERROR_MAP[appErr.code ?? ""];
      setError(mapped ?? appErr.message ?? "下单失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
      <h3 className="text-title-card mb-md">快捷下单</h3>

      {/* 买/卖切换 */}
	      <div className="flex gap-xs mb-md">
	        <button
	          type="button"
	          onClick={() => setSide("BUY")}
	          className={`flex-1 py-sm rounded-md text-body font-medium transition-all duration-120 ease-out ${
	            side === "BUY"
	              ? "bg-state-up/10 text-state-up border border-state-up/30"
	              : "bg-bg-subtle text-text-secondary border border-secondary-300/20 hover:opacity-92"
	          }`}
	        >
	          买入
	        </button>
	        <button
	          type="button"
	          onClick={() => setSide("SELL")}
	          className={`flex-1 py-sm rounded-md text-body font-medium transition-all duration-120 ease-out ${
	            side === "SELL"
	              ? "bg-state-down/10 text-state-down border border-state-down/30"
	              : "bg-bg-subtle text-text-secondary border border-secondary-300/20 hover:opacity-92"
	          }`}
	        >
	          卖出
        </button>
      </div>

      <div className="flex flex-col gap-md">
	        <TextField
	          label="标的代码"
	          placeholder="例如 AAPL"
	          value={symbol}
	          onChange={(e: ChangeEvent<HTMLInputElement>) =>
	            setSymbol(e.target.value)
	          }
	        />
	        <div className="grid grid-cols-2 gap-md">
	          <TextField
	            label="数量"
	            type="number"
	            placeholder="0"
	            value={quantity}
	            onChange={(e: ChangeEvent<HTMLInputElement>) =>
	              setQuantity(e.target.value)
	            }
	          />
	          <TextField
	            label="价格"
	            type="number"
	            placeholder="0.00"
	            value={price}
	            onChange={(e: ChangeEvent<HTMLInputElement>) =>
	              setPrice(e.target.value)
	            }
	          />
	        </div>

        {/* 预估金额 */}
        {quantity &&
          price &&
          !Number.isNaN(parseFloat(quantity) * parseFloat(price)) && (
            <p className="text-caption text-text-secondary">
              预估金额：
              <span className="text-data-mono">
                ¥
                {(parseFloat(quantity) * parseFloat(price)).toLocaleString(
                  "zh-CN",
                  { minimumFractionDigits: 2, maximumFractionDigits: 2 },
                )}
              </span>
            </p>
          )}

        {error && (
          <p className="text-body text-state-risk" role="alert">
            {error}
          </p>
        )}

        <Button
          loading={submitting}
          onClick={() => void handleSubmit()}
          className="w-full"
        >
          {side === "BUY" ? "确认买入" : "确认卖出"}
        </Button>
      </div>
    </div>
  );
}
