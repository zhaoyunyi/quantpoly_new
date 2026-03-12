/**
 * /strategies/advanced — 高级分析入口
 *
 * 功能：
 * - 对比、研究任务入口目录页
 * - 研究任务：性能分析、参数优化
 * - 查看研究结果
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategies,
  submitResearchPerformanceTask,
  submitResearchOptimizationTask,
  getResearchResults,
} from "@qp/api-client";
import type {
  StrategyItem,
  ResearchTaskResult,
  AppError,
} from "@qp/api-client";
import {
  Button,
  Select,
  TextField,
  Dialog,
  Skeleton,
  EmptyState,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  useToast,
} from "@qp/ui";
import { StrategyStatusBadge } from "../../widgets/strategies/StrategyStatusBadge";

export const Route = createFileRoute("/strategies/advanced")({
  component: StrategyAdvancedPage,
});

export function StrategyAdvancedPage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState("");

  /* ─── 研究任务 ─── */
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [taskType, setTaskType] = useState<"performance" | "optimization">(
    "performance",
  );
  const [analysisDays, setAnalysisDays] = useState("30");
  const [submitting, setSubmitting] = useState(false);
  const [taskResult, setTaskResult] = useState<ResearchTaskResult | null>(null);

  /* ─── 研究结果列表 ─── */
  const [results, setResults] = useState<Array<Record<string, unknown>>>([]);
  const [resultsLoading, setResultsLoading] = useState(false);

  const loadStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getStrategies({ pageSize: 200 });
      setStrategies(result.items);
    } catch {
      toast.show("加载策略失败", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadStrategies();
  }, [loadStrategies]);

  const loadResults = useCallback(async (strategyId: string) => {
    setResultsLoading(true);
    try {
      const data = await getResearchResults(strategyId);
      setResults(data.items);
    } catch {
      // 研究结果加载失败不阻塞
      setResults([]);
    } finally {
      setResultsLoading(false);
    }
  }, []);

  const handleSelectStrategy = (id: string) => {
    setSelectedId(id);
    if (id) void loadResults(id);
  };

  const handleOpenTask = (type: "performance" | "optimization") => {
    if (!selectedId) {
      toast.show("请先选择一个策略", "warning");
      return;
    }
    setTaskType(type);
    setTaskResult(null);
    setTaskDialogOpen(true);
  };

  const handleSubmitTask = async () => {
    if (!selectedId) return;
    setSubmitting(true);
    try {
      let result: ResearchTaskResult;
      if (taskType === "performance") {
        result = await submitResearchPerformanceTask(selectedId, {
          analysisPeriodDays: parseInt(analysisDays, 10) || 30,
        });
      } else {
        result = await submitResearchOptimizationTask(selectedId, {});
      }
      setTaskResult(result);
      toast.show("研究任务已提交", "success");
      // 刷新结果列表
      void loadResults(selectedId);
    } catch (err) {
      toast.show((err as AppError).message || "任务提交失败", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const strategyOptions = strategies.map((s) => ({
    value: s.id,
    label: `${s.name} (${s.template})`,
  }));

  const selectedStrategy = strategies.find((s) => s.id === selectedId);

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 标题 */}
        <header>
          <button
            type="button"
            className="text-primary-500 hover:text-primary-700 text-body transition-all duration-[120ms] ease-out"
            onClick={() => void navigate({ to: "/strategies" })}
          >
            ← 返回策略列表
          </button>
          <h1 className="text-title-page mt-xs">高级分析</h1>
          <p className="text-body-secondary mt-xs">
            深度分析策略性能、参数优化与策略对比。
          </p>
        </header>

        {/* 快捷入口 */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-md">
          <EntryCard
            title="策略对比"
            description="比较多个策略的回测指标表现"
            onClick={() => void navigate({ to: "/strategies/compare" })}
          />
          <EntryCard
            title="性能分析"
            description="提交策略性能分析研究任务"
            onClick={() => handleOpenTask("performance")}
          />
          <EntryCard
            title="参数优化"
            description="提交策略参数优化研究任务"
            onClick={() => handleOpenTask("optimization")}
          />
        </section>

        {/* 策略选择 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">选择策略</h2>
          {loading ? (
            <Skeleton width="100%" height="40px" />
          ) : (
            <div className="flex items-end gap-md">
              <Select
                label="策略"
                options={strategyOptions}
                value={selectedId}
                onValueChange={handleSelectStrategy}
                placeholder="选择要分析的策略"
                className="flex-1"
              />
              {selectedStrategy && (
                <StrategyStatusBadge status={selectedStrategy.status} />
              )}
            </div>
          )}
        </section>

        {/* 研究结果 */}
        {selectedId && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">研究结果</h2>
            {resultsLoading ? (
              <div className="flex flex-col gap-sm">
                {Array.from({ length: 3 }).map((_, idx) => (
                  <Skeleton key={idx} width="100%" height="36px" />
                ))}
              </div>
            ) : results.length === 0 ? (
              <EmptyState
                title="暂无研究结果"
                description="请提交研究任务后查看结果。"
              />
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>任务 ID</TableHeaderCell>
                    <TableHeaderCell>类型</TableHeaderCell>
                    <TableHeaderCell>状态</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.map((r, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <span className="text-data-mono text-caption">
                          {String(r.taskId ?? r.id ?? idx)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-caption">
                          {String(r.taskType ?? "-")}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-caption">
                          {String(r.status ?? "-")}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </section>
        )}

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>

      {/* 研究任务对话框 */}
      <Dialog
        open={taskDialogOpen}
        onOpenChange={setTaskDialogOpen}
        title={
          taskType === "performance" ? "提交性能分析任务" : "提交参数优化任务"
        }
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setTaskDialogOpen(false)}
              disabled={submitting}
            >
              取消
            </Button>
            <Button
              loading={submitting}
              onClick={() => void handleSubmitTask()}
            >
              提交
            </Button>
          </>
        }
      >
        {taskResult ? (
          <div className="flex flex-col gap-sm">
            <p className="text-body text-text-primary">任务已提交成功。</p>
            <div className="flex gap-md text-caption text-text-secondary">
              <span>ID: {taskResult.taskId}</span>
              <span>状态: {taskResult.status}</span>
            </div>
          </div>
        ) : taskType === "performance" ? (
          <TextField
            label="分析周期（天）"
            type="number"
            value={analysisDays}
            onChange={(e) => setAnalysisDays(e.target.value)}
            help="1-365 天"
          />
        ) : (
          <p className="text-body-secondary">
            将使用默认参数空间和目标函数提交优化任务。
          </p>
        )}
      </Dialog>
    </ProtectedLayout>
  );
}

function EntryCard({
  title,
  description,
  onClick,
}: {
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col gap-xs p-lg bg-bg-card rounded-md shadow-card border border-secondary-300/20 text-left transition-all duration-[120ms] ease-out hover:opacity-92 hover:border-primary-500/30"
    >
      <span className="text-title-card">{title}</span>
      <span className="text-body-secondary">{description}</span>
    </button>
  );
}
