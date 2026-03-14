/**
 * /strategies/compare — 多策略对比页
 *
 * 功能：
 * - 选择 2-5 个策略
 * - 为每个策略选取对比用 backtest（默认最新 completed）
 * - 调用 POST /backtests/compare 并展示对比表
 * - 支持 CSV 导出
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategies,
  getStrategyBacktests,
  compareBacktests,
} from "@qp/api-client";
import type { StrategyItem, StrategyBacktest, AppError } from "@qp/api-client";
import { Button, Skeleton, EmptyState, useToast } from "@qp/ui";
import {
  CompareMatrix,
  type CompareMetricRow,
} from "../../widgets/strategies/CompareMatrix";

export const Route = createFileRoute("/strategies/compare")({
  component: StrategyComparePage,
});

const MAX_COMPARE = 5;
const MIN_COMPARE = 2;

export function StrategyComparePage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<{
    names: string[];
    metrics: CompareMetricRow[];
  } | null>(null);

  const loadStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getStrategies({ pageSize: 200 });
      setStrategies(result.items);
    } catch {
      toast.show("加载策略列表失败", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadStrategies();
  }, [loadStrategies]);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < MAX_COMPARE) {
        next.add(id);
      }
      return next;
    });
  };

  const handleCompare = async () => {
    if (selectedIds.size < MIN_COMPARE) {
      toast.show(`请至少选择 ${MIN_COMPARE} 个策略进行对比`, "warning");
      return;
    }

    setComparing(true);
    setCompareResult(null);
    try {
      // 为每个策略获取最新 completed 回测
      const ids = Array.from(selectedIds);
      const backtestRequests = ids.map(async (sid) => {
        try {
          const btResult = await getStrategyBacktests(sid, {
            status: "completed",
            page: 1,
            pageSize: 1,
          });
          return { strategyId: sid, backtest: btResult.items[0] ?? null };
        } catch {
          return { strategyId: sid, backtest: null };
        }
      });
      const backtestResults = await Promise.all(backtestRequests);

      const validBacktests = backtestResults.filter((r) => r.backtest !== null);
      if (validBacktests.length < MIN_COMPARE) {
        toast.show("所选策略中没有足够的已完成回测用于对比", "warning");
        setComparing(false);
        return;
      }

      const taskIds = validBacktests.map((r) => r.backtest!.id);
      const result = await compareBacktests(taskIds);

      // 构造对比矩阵数据
      const names = validBacktests.map((r) => {
        const s = strategies.find((s) => s.id === r.strategyId);
        return s?.name ?? r.strategyId;
      });

      const metricKeys = new Set<string>();
      for (const m of result.metrics) {
        for (const key of Object.keys(m)) {
          metricKeys.add(key);
        }
      }

      const metricRows: CompareMetricRow[] = Array.from(metricKeys).map(
        (key) => ({
          label: key,
          values: result.metrics.map((m) => formatMetricValue(m[key])),
        }),
      );

      setCompareResult({ names, metrics: metricRows });
    } catch (err) {
      toast.show((err as AppError).message || "对比失败", "error");
    } finally {
      setComparing(false);
    }
  };

  const handleExportCsv = () => {
    if (!compareResult) return;
    const header = ["指标", ...compareResult.names].join(",");
    const rows = compareResult.metrics.map((row) =>
      [row.label, ...row.values].join(","),
    );
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "strategy-compare.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题 */}
        <header>
          <button
            type="button"
            className="text-primary-500 hover:text-primary-700 text-body transition-all duration-120 ease-out"
            onClick={() => void navigate({ to: "/strategies" })}
          >
            ← 返回策略列表
          </button>
          <h1 className="text-title-page mt-xs">策略对比</h1>
          <p className="text-body-secondary mt-xs">
            选择 {MIN_COMPARE}-{MAX_COMPARE}{" "}
            个策略，基于最近完成的回测进行指标对比。
          </p>
        </header>

        {/* 策略选择 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">选择策略</h2>
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-sm">
              {Array.from({ length: 4 }).map((_, idx) => (
                <Skeleton key={idx} width="100%" height="48px" />
              ))}
            </div>
          ) : strategies.length === 0 ? (
            <EmptyState
              title="暂无策略"
              description="请先创建策略后再进行对比。"
            />
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-sm mb-md">
                {strategies.map((s) => {
                  const isSelected = selectedIds.has(s.id);
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => toggleSelect(s.id)}
                      className={`flex items-center gap-sm p-sm rounded-md border text-left transition-all duration-120 ease-out ${
                        isSelected
                          ? "border-primary-500 bg-primary-500/5"
                          : "border-secondary-300/20 hover:border-secondary-300/40"
                      }`}
                    >
                      <span
                        className={`w-5 h-5 rounded-sm border flex items-center justify-center transition-all duration-120 ease-out ${
                          isSelected
                            ? "bg-primary-700 border-primary-700 text-white"
                            : "border-secondary-300/40"
                        }`}
                      >
                        {isSelected && (
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 16 16"
                            fill="none"
                            aria-hidden="true"
                          >
                            <path
                              d="M3 8l4 4 6-6"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        )}
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className="text-body font-medium truncate block">
                          {s.name}
                        </span>
                        <span className="text-caption text-text-muted">
                          {s.template}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="flex items-center gap-sm">
                <span className="text-caption text-text-muted">
                  已选择 {selectedIds.size}/{MAX_COMPARE}
                </span>
                <Button
                  loading={comparing}
                  disabled={selectedIds.size < MIN_COMPARE}
                  onClick={() => void handleCompare()}
                >
                  开始对比
                </Button>
              </div>
            </>
          )}
        </section>

        {/* 对比结果 */}
        {compareResult && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <div className="flex items-center justify-between mb-md">
              <h2 className="text-title-section">对比结果</h2>
              <Button variant="secondary" size="sm" onClick={handleExportCsv}>
                导出 CSV
              </Button>
            </div>
            <CompareMatrix
              strategyNames={compareResult.names}
              metrics={compareResult.metrics}
            />
          </section>
        )}

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  );
}

function formatMetricValue(val: unknown): string {
  if (val === null || val === undefined) return "-";
  if (typeof val === "number") {
    return Number.isFinite(val)
      ? val.toLocaleString("zh-CN", { maximumFractionDigits: 4 })
      : "-";
  }
  return String(val);
}
