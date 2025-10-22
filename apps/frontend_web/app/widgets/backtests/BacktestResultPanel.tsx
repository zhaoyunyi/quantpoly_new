/**
 * 回测结果面板组件
 *
 * 展示回测指标卡片 + 图表占位 + 未就绪时的提示刷新入口。
 * 处理 BACKTEST_RESULT_NOT_READY 状态。
 */

import { Button, Skeleton, EmptyState } from "@qp/ui";
import type { BacktestResult, BacktestStatus } from "@qp/api-client";

export interface BacktestResultPanelProps {
  result: BacktestResult | null;
  status: BacktestStatus;
  loading?: boolean;
  notReady?: boolean;
  onRefresh?: () => void;
}

interface MetricCardProps {
  label: string;
  value: string;
  risk?: boolean;
}

function MetricCard({ label, value, risk }: MetricCardProps) {
  return (
    <div className="flex flex-col gap-xs bg-bg-subtle rounded-md p-md">
      <span className="text-caption text-text-secondary">{label}</span>
      <span
        className={`text-data-primary ${risk ? "state-risk" : ""}`}
        data-mono
      >
        {value}
      </span>
    </div>
  );
}

export function BacktestResultPanel({
  result,
  status,
  loading,
  notReady,
  onRefresh,
}: BacktestResultPanelProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-md">
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-md">
          {Array.from({ length: 5 }).map((_, idx) => (
            <Skeleton key={idx} width="100%" height="72px" />
          ))}
        </div>
        <Skeleton width="100%" height="200px" />
      </div>
    );
  }

  /* 结果未就绪 */
  if (notReady || (status !== "completed" && !result)) {
    const statusMessages: Record<string, { title: string; desc: string }> = {
      pending: {
        title: "回测排队中",
        desc: "任务已提交，正在等待执行。",
      },
      running: {
        title: "回测运行中",
        desc: "结果生成中，请稍后刷新查看。",
      },
      failed: {
        title: "回测失败",
        desc: "回测执行过程中出现错误，可尝试重试。",
      },
      cancelled: {
        title: "回测已取消",
        desc: "此回测任务已被取消。",
      },
    };

    const msg = statusMessages[status] ?? {
      title: "结果未就绪",
      desc: "回测结果尚未生成，请稍后刷新。",
    };

    return (
      <EmptyState
        title={msg.title}
        description={msg.desc}
        action={
          onRefresh ? (
            <Button variant="secondary" onClick={onRefresh}>
              刷新结果
            </Button>
          ) : undefined
        }
      />
    );
  }

  if (!result) {
    return (
      <EmptyState
        title="暂无结果数据"
        description="回测结果为空。"
        action={
          onRefresh ? (
            <Button variant="secondary" onClick={onRefresh}>
              刷新
            </Button>
          ) : undefined
        }
      />
    );
  }

  const metrics = result.metrics ?? {};

  return (
    <div className="flex flex-col gap-lg">
      {/* 指标卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-md">
        <MetricCard label="收益率" value={fmtPct(metrics.returnRate)} />
        <MetricCard
          label="最大回撤"
          value={fmtPct(metrics.maxDrawdown)}
          risk={(metrics.maxDrawdown ?? 0) > 0.2}
        />
        <MetricCard label="夏普比率" value={fmtNum(metrics.sharpeRatio)} />
        <MetricCard label="交易次数" value={fmtInt(metrics.tradeCount)} />
        <MetricCard label="胜率" value={fmtPct(metrics.winRate)} />
      </div>

      {/* 图表占位 */}
      <div className="bg-bg-subtle rounded-md p-lg flex items-center justify-center min-h-[200px]">
        <p className="text-body-secondary text-text-muted">
          权益曲线图表（待接入图表库后启用）
        </p>
      </div>
    </div>
  );
}

function fmtPct(val: unknown): string {
  if (val === null || val === undefined) return "-";
  const num = Number(val);
  if (!Number.isFinite(num)) return "-";
  return `${(num * 100).toFixed(2)}%`;
}

function fmtNum(val: unknown): string {
  if (val === null || val === undefined) return "-";
  const num = Number(val);
  if (!Number.isFinite(num)) return "-";
  return num.toFixed(2);
}

function fmtInt(val: unknown): string {
  if (val === null || val === undefined) return "-";
  const num = Number(val);
  if (!Number.isFinite(num)) return "-";
  return num.toLocaleString("zh-CN");
}
