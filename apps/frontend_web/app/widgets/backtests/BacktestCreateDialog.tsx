/**
 * 回测创建对话框（表单 Widget）
 *
 * 最小表单：选择策略 + 配置参数（时间范围/初始资金/标的/频率）。
 * 提交后调用 POST /backtests 创建回测任务。
 */

import { useState, type ChangeEvent } from "react";
import { Button, TextField, Select, Dialog } from "@qp/ui";
import type { StrategyItem } from "@qp/api-client";

export interface BacktestCreateFormData {
  strategyId: string;
  config: {
    startDate: string;
    endDate: string;
    initialCapital: number;
    symbols: string;
    frequency: string;
  };
}

export interface BacktestCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategies: StrategyItem[];
  onSubmit: (data: BacktestCreateFormData) => void;
  loading?: boolean;
}

const FREQUENCY_OPTIONS = [
  { value: "1d", label: "日线" },
  { value: "1h", label: "1小时" },
  { value: "30m", label: "30分钟" },
  { value: "15m", label: "15分钟" },
  { value: "5m", label: "5分钟" },
];

const today = () => {
  const d = new Date();
  return d.toISOString().split("T")[0];
};

const oneYearAgo = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().split("T")[0];
};

export function BacktestCreateDialog({
  open,
  onOpenChange,
  strategies,
  onSubmit,
  loading,
}: BacktestCreateDialogProps) {
  const [strategyId, setStrategyId] = useState("");
  const [startDate, setStartDate] = useState(oneYearAgo);
  const [endDate, setEndDate] = useState(today);
  const [initialCapital, setInitialCapital] = useState("1000000");
  const [symbols, setSymbols] = useState("000001.SZ");
  const [frequency, setFrequency] = useState("1d");

  const strategyOptions = strategies.map((s) => ({
    value: s.id,
    label: s.name,
  }));

  const handleSubmit = () => {
    if (!strategyId) return;
    onSubmit({
      strategyId,
      config: {
        startDate,
        endDate,
        initialCapital: Number(initialCapital) || 1_000_000,
        symbols,
        frequency,
      },
    });
  };

  const canSubmit = !!strategyId && !!startDate && !!endDate;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="创建回测"
      description="选择策略并配置回测参数。"
      footer={
        <>
          <Button
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            loading={loading}
            disabled={!canSubmit}
          >
            提交回测
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-md">
        <Select
          label="策略"
          options={[{ value: "", label: "请选择策略…" }, ...strategyOptions]}
          value={strategyId}
          onValueChange={setStrategyId}
        />
        <div className="grid grid-cols-2 gap-md">
          <TextField
            label="开始日期"
            type="date"
            value={startDate}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setStartDate(e.target.value)
            }
          />
          <TextField
            label="结束日期"
            type="date"
            value={endDate}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setEndDate(e.target.value)
            }
          />
        </div>
        <TextField
          label="初始资金"
          type="number"
          value={initialCapital}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setInitialCapital(e.target.value)
          }
          placeholder="1000000"
        />
        <TextField
          label="标的代码"
          value={symbols}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setSymbols(e.target.value)
          }
          placeholder="000001.SZ"
        />
        <Select
          label="频率"
          options={FREQUENCY_OPTIONS}
          value={frequency}
          onValueChange={setFrequency}
        />
      </div>
    </Dialog>
  );
}
