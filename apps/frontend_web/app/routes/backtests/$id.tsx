/**
 * /backtests/$id — 回测详情页
 *
 * 功能：
 * - 回测任务详情展示
 * - 回测结果与指标卡片
 * - 处理 BACKTEST_RESULT_NOT_READY（展示提示 + 刷新入口）
 * - 关联回测列表（同策略的其他回测）
 * - 操作：取消 / 重试 / 重命名
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getBacktest,
  getBacktestResult,
  getRelatedBacktests,
  cancelBacktest,
  retryBacktest,
  renameBacktest,
} from "@qp/api-client";
import type { BacktestTask, BacktestResult, AppError } from "@qp/api-client";
import { Button, Skeleton, EmptyState, useToast } from "@qp/ui";
import { BacktestStatusBadge } from "../../widgets/backtests/BacktestStatusBadge";
import { BacktestResultPanel } from "../../widgets/backtests/BacktestResultPanel";
import { BacktestActions } from "../../widgets/backtests/BacktestActions";

export const Route = createFileRoute("/backtests/$id")({
  component: BacktestDetailPage,
});

const POLL_INTERVAL_MS = 5_000;

export function BacktestDetailPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const toast = useToast();

  /* ─── 任务详情 ─── */
  const [task, setTask] = useState<BacktestTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppError | null>(null);

  /* ─── 回测结果 ─── */
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [resultLoading, setResultLoading] = useState(false);
  const [resultNotReady, setResultNotReady] = useState(false);

  /* ─── 关联回测 ─── */
  const [relatedTasks, setRelatedTasks] = useState<BacktestTask[]>([]);
  const [relatedLoading, setRelatedLoading] = useState(true);

  /* ─── 轮询 ─── */
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const loadTask = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const t = await getBacktest(id);
      setTask(t);
    } catch (err) {
      setError(err as AppError);
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadResult = useCallback(async () => {
    setResultLoading(true);
    setResultNotReady(false);
    try {
      const r = await getBacktestResult(id);
      setResult(r);
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.code === "BACKTEST_RESULT_NOT_READY") {
        setResultNotReady(true);
      }
      // 其他错误静默——结果面板会根据 notReady + status 展示
    } finally {
      setResultLoading(false);
    }
  }, [id]);

  const loadRelated = useCallback(async () => {
    setRelatedLoading(true);
    try {
      const items = await getRelatedBacktests(id, { limit: 10 });
      setRelatedTasks(items);
    } catch {
      // 非关键，静默
    } finally {
      setRelatedLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadTask();
    void loadResult();
    void loadRelated();
  }, [loadTask, loadResult, loadRelated]);

  /* 轮询：pending/running 时自动刷新 */
  useEffect(() => {
    const shouldPoll = task?.status === "pending" || task?.status === "running";
    if (shouldPoll) {
      pollRef.current = setInterval(() => {
        void (async () => {
          try {
            const t = await getBacktest(id);
            setTask(t);
            if (t.status === "completed" || t.status === "failed") {
              void loadResult();
              if (pollRef.current) clearInterval(pollRef.current);
            }
          } catch {
            // 静默
          }
        })();
      }, POLL_INTERVAL_MS);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [task?.status, id, loadResult]);

  /* ─── 操作 ─── */
  const handleCancel = async () => {
    try {
      const updated = await cancelBacktest(id);
      setTask(updated);
      toast.show("回测已取消", "success");
    } catch (err) {
      toast.show((err as AppError).message || "取消失败", "error");
    }
  };

  const handleRetry = async () => {
    try {
      const updated = await retryBacktest(id);
      setTask(updated);
      toast.show("回测已重新排队", "success");
    } catch (err) {
      toast.show((err as AppError).message || "重试失败", "error");
    }
  };

  const handleRename = async (_taskId: string, newName: string) => {
    try {
      const updated = await renameBacktest(id, { displayName: newName });
      setTask(updated);
      toast.show("重命名成功", "success");
    } catch (err) {
      toast.show((err as AppError).message || "重命名失败", "error");
    }
  };

  /* ─── 渲染 ─── */
  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex flex-col gap-lg">
          <Skeleton width="40%" height="32px" />
          <Skeleton width="100%" height="200px" />
          <Skeleton width="100%" height="150px" />
        </div>
      </ProtectedLayout>
    );
  }

  if (error || !task) {
    return (
      <ProtectedLayout>
        <EmptyState
          title="回测不存在"
          description={error?.message || "未能加载回测详情"}
          action={
            <Button
              variant="secondary"
              onClick={() => void navigate({ to: "/backtests" })}
            >
              返回列表
            </Button>
          }
        />
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题栏 */}
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-sm">
              <button
                type="button"
                className="text-primary-500 hover:text-primary-700 text-body transition-all duration-120 ease-out"
                onClick={() => void navigate({ to: "/backtests" })}
              >
                ← 回测列表
              </button>
            </div>
            <h1 className="text-title-page mt-xs">
              {task.displayName || `回测 ${task.id.slice(0, 12)}`}
            </h1>
            <div className="flex items-center gap-sm mt-xs flex-wrap">
              <BacktestStatusBadge status={task.status} />
              <span className="text-caption text-text-muted">
                策略: {task.strategyId.slice(0, 12)}
              </span>
              <span className="text-data-mono text-text-muted">
                创建于 {formatDate(task.createdAt)}
              </span>
              <span className="text-data-mono text-text-muted">
                更新于 {formatDate(task.updatedAt)}
              </span>
            </div>
          </div>
          <div className="shrink-0">
            <BacktestActions
              taskId={task.id}
              status={task.status}
              displayName={task.displayName}
              onCancel={() => void handleCancel()}
              onRetry={() => void handleRetry()}
              onRename={(tid, name) => void handleRename(tid, name)}
            />
          </div>
        </header>

        {/* 配置信息 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">回测配置</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-md">
            {Object.entries(task.config).map(([key, value]) => (
              <div key={key} className="flex flex-col gap-xs">
                <span className="text-caption text-text-secondary">{key}</span>
                <span className="text-data-mono text-body">
                  {String(value)}
                </span>
              </div>
            ))}
            {Object.keys(task.config).length === 0 && (
              <p className="text-body-secondary text-text-muted col-span-full">
                使用默认配置
              </p>
            )}
          </div>
        </section>

        {/* 回测结果 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">回测结果</h2>
          <BacktestResultPanel
            result={result}
            status={task.status}
            loading={resultLoading}
            notReady={resultNotReady}
            onRefresh={() => void loadResult()}
          />
        </section>

        {/* 关联回测 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">相关回测</h2>
          {relatedLoading ? (
            <div className="flex flex-col gap-sm">
              {Array.from({ length: 3 }).map((_, idx) => (
                <Skeleton key={idx} width="100%" height="36px" />
              ))}
            </div>
          ) : relatedTasks.length === 0 ? (
            <p className="text-body-secondary text-text-muted">
              暂无同策略的其他回测任务。
            </p>
          ) : (
            <div className="flex flex-col gap-sm">
              {relatedTasks.map((rt) => (
                <button
                  key={rt.id}
                  type="button"
                  onClick={() =>
                    void navigate({
                      to: "/backtests/$id",
                      params: { id: rt.id },
                    })
                  }
                  className="flex items-center gap-md p-sm rounded-md border border-secondary-300/20 hover:border-secondary-300/40 transition-all duration-120 ease-out text-left"
                >
                  <span className="text-data-mono text-caption text-primary-500 min-w-[100px]">
                    {rt.displayName || rt.id.slice(0, 12)}
                  </span>
                  <BacktestStatusBadge status={rt.status} />
                  <span className="text-data-mono text-text-muted text-caption">
                    {formatDate(rt.createdAt)}
                  </span>
                  {rt.metrics?.returnRate != null && (
                    <span className="text-data-mono text-caption ml-auto">
                      收益 {fmtPct(rt.metrics.returnRate as number)}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </section>

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  );
}

/* ─── 辅助函数 ─── */

function formatDate(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

function fmtPct(val: number): string {
  if (!Number.isFinite(val)) return "0.00%";
  return `${(val * 100).toFixed(2)}%`;
}
