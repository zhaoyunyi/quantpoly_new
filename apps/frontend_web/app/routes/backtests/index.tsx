/**
 * /backtests — 回测中心列表页
 *
 * 功能：
 * - 搜索、筛选（status）、分页
 * - 统计概览卡片
 * - 创建回测（选择策略 + 参数配置）
 * - 行操作：查看 / 取消 / 重试 / 重命名 / 删除
 * - 多选对比：选取多个 backtest taskId → POST /backtests/compare
 * - 运行中任务自动轮询刷新
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getBacktests,
  getBacktestStatistics,
  getStrategies,
  createBacktest,
  cancelBacktest,
  retryBacktest,
  renameBacktest,
  deleteBacktest,
  compareBacktests,
} from "@qp/api-client";
import type {
  BacktestTask,
  BacktestStatistics,
  StrategyItem,
  AppError,
} from "@qp/api-client";
import { Button, Dialog, Select, Skeleton, EmptyState, useToast } from "@qp/ui";
import { BacktestTable } from "../../widgets/backtests/BacktestTable";
import {
  BacktestCreateDialog,
  type BacktestCreateFormData,
} from "../../widgets/backtests/BacktestCreateDialog";
import { Pagination } from "../../widgets/strategies/Pagination";
import {
  CompareMatrix,
  type CompareMetricRow,
} from "../../widgets/strategies/CompareMatrix";

export const Route = createFileRoute("/backtests/")({
  component: BacktestsListPage,
});

const PAGE_SIZE = 20;
const POLL_INTERVAL_MS = 8_000;

const STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "排队中" },
  { value: "running", label: "运行中" },
  { value: "completed", label: "已完成" },
  { value: "failed", label: "失败" },
  { value: "cancelled", label: "已取消" },
];

export function BacktestsListPage() {
  const navigate = useNavigate();
  const toast = useToast();

  /* ─── 列表状态 ─── */
  const [items, setItems] = useState<BacktestTask[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppError | null>(null);

  /* ─── 统计 ─── */
  const [stats, setStats] = useState<BacktestStatistics | null>(null);

  /* ─── 筛选 ─── */
  const [statusFilter, setStatusFilter] = useState("");

  /* ─── 创建对话框 ─── */
  const [createOpen, setCreateOpen] = useState(false);
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [creating, setCreating] = useState(false);

  /* ─── 多选对比 ─── */
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<{
    names: string[];
    metrics: CompareMetricRow[];
  } | null>(null);

  /* ─── 删除确认 ─── */
  const [deleteTarget, setDeleteTarget] = useState<BacktestTask | null>(null);
  const [deleting, setDeleting] = useState(false);

  /* ─── 轮询 ─── */
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  /* ─── 数据加载 ─── */
  const loadList = useCallback(
    async (p: number, status: string, silent?: boolean) => {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      try {
        const [result, statsData] = await Promise.all([
          getBacktests({
            page: p,
            pageSize: PAGE_SIZE,
            status: status || undefined,
          }),
          getBacktestStatistics(),
        ]);
        setItems(result.items);
        setTotal(result.total);
        setPage(result.page);
        setStats(statsData);
      } catch (err) {
        if (!silent) setError(err as AppError);
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadList(1, statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* 轮询：当有 pending/running 时自动刷新 */
  useEffect(() => {
    const hasPendingOrRunning = items.some(
      (t) => t.status === "pending" || t.status === "running",
    );
    if (hasPendingOrRunning) {
      pollRef.current = setInterval(() => {
        void loadList(page, statusFilter, true);
      }, POLL_INTERVAL_MS);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [items, page, statusFilter, loadList]);

  const handleStatusChange = (val: string) => {
    setStatusFilter(val);
    void loadList(1, val);
  };

  const handlePageChange = (p: number) => {
    void loadList(p, statusFilter);
  };

  const reload = () => void loadList(page, statusFilter);

  /* ─── 行操作 ─── */
  const handleView = (id: string) =>
    void navigate({ to: "/backtests/$id", params: { id } });

  const handleCancel = async (id: string) => {
    try {
      await cancelBacktest(id);
      toast.show("回测已取消", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "取消失败", "error");
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await retryBacktest(id);
      toast.show("回测已重新排队", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "重试失败", "error");
    }
  };

  const handleRename = async (id: string, newName: string) => {
    try {
      await renameBacktest(id, { displayName: newName });
      toast.show("重命名成功", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "重命名失败", "error");
    }
  };

  const handleDeleteRequest = (id: string) => {
    const item = items.find((i) => i.id === id);
    if (item) setDeleteTarget(item);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteBacktest(deleteTarget.id);
      toast.show("回测已删除", "success");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.code === "BACKTEST_DELETE_INVALID_STATE") {
        toast.show("运行中的回测无法删除，请先取消", "error");
      } else {
        toast.show(appErr.message || "删除失败", "error");
      }
    } finally {
      setDeleting(false);
    }
  };

  /* ─── 创建回测 ─── */
  const handleOpenCreate = async () => {
    setCreateOpen(true);
    try {
      const result = await getStrategies({ pageSize: 200 });
      setStrategies(result.items);
    } catch {
      toast.show("加载策略列表失败", "error");
    }
  };

  const handleCreate = async (data: BacktestCreateFormData) => {
    setCreating(true);
    try {
      await createBacktest({
        strategyId: data.strategyId,
        config: data.config as Record<string, unknown>,
      });
      toast.show("回测已创建", "success");
      setCreateOpen(false);
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "创建失败", "error");
    } finally {
      setCreating(false);
    }
  };

  /* ─── 多选对比 ─── */
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < 5) {
        next.add(id);
      }
      return next;
    });
  };

  const handleCompare = async () => {
    if (selectedIds.size < 2) {
      toast.show("请至少选择 2 个回测任务进行对比", "warning");
      return;
    }
    setComparing(true);
    setCompareResult(null);
    try {
      const taskIds = Array.from(selectedIds);
      const result = await compareBacktests(taskIds);

      const names = taskIds.map((tid) => {
        const t = items.find((i) => i.id === tid);
        return t?.displayName || tid.slice(0, 12);
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
    a.download = "backtest-compare.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 页面标题 */}
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <h1 className="text-title-page">回测中心</h1>
            <p className="text-body-secondary mt-xs">
              管理与追踪回测任务，对比多组回测结果。
            </p>
          </div>
          <div className="shrink-0 flex gap-sm">
            <Button onClick={() => void handleOpenCreate()}>创建回测</Button>
          </div>
        </header>

        {/* 统计概览 */}
        {stats && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">统计概览</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-md">
              <StatItem label="总计" value={stats.totalCount} />
              <StatItem label="排队中" value={stats.pendingCount} />
              <StatItem label="运行中" value={stats.runningCount} />
              <StatItem label="已完成" value={stats.completedCount} />
              <StatItem label="失败" value={stats.failedCount} />
              <StatItem
                label="平均收益率"
                value={fmtPct(stats.averageReturnRate)}
              />
              <StatItem
                label="平均最大回撤"
                value={fmtPct(stats.averageMaxDrawdown)}
                risk={stats.averageMaxDrawdown > 0.2}
              />
              <StatItem label="平均胜率" value={fmtPct(stats.averageWinRate)} />
            </div>
          </section>
        )}

        {/* 筛选 + 对比操作 */}
        <div className="flex items-end gap-md flex-wrap">
          <Select
            label="状态"
            options={STATUS_OPTIONS}
            value={statusFilter}
            onValueChange={handleStatusChange}
            className="w-40"
          />
          <div className="flex-1" />
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-sm">
              <span className="text-caption text-text-muted">
                已选 {selectedIds.size}/5
              </span>
              <Button
                variant="secondary"
                loading={comparing}
                disabled={selectedIds.size < 2}
                onClick={() => void handleCompare()}
              >
                对比选中
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedIds(new Set())}
              >
                清除选择
              </Button>
            </div>
          )}
        </div>

        {/* 表格 */}
        {loading && items.length === 0 ? (
          <div className="flex flex-col gap-sm">
            {Array.from({ length: 5 }).map((_, idx) => (
              <Skeleton key={idx} width="100%" height="48px" />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            title="加载失败"
            description={error.message || "无法获取回测列表"}
            action={
              <Button variant="secondary" onClick={reload}>
                重试
              </Button>
            }
          />
        ) : (
          <>
            <BacktestTable
              items={items}
              loading={loading}
              selectedIds={selectedIds}
              onToggleSelect={handleToggleSelect}
              onView={handleView}
              onCancel={(id) => void handleCancel(id)}
              onRetry={(id) => void handleRetry(id)}
              onRename={(id, name) => void handleRename(id, name)}
              onDelete={handleDeleteRequest}
            />
            {total > PAGE_SIZE && (
              <Pagination
                page={page}
                pageSize={PAGE_SIZE}
                total={total}
                onPageChange={handlePageChange}
              />
            )}
          </>
        )}

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

      {/* 创建回测对话框 */}
      <BacktestCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        strategies={strategies}
        onSubmit={(data) => void handleCreate(data)}
        loading={creating}
      />

      {/* 删除确认对话框 */}
      {deleteTarget && (
        <DeleteConfirmDialog
          item={deleteTarget}
          deleting={deleting}
          onConfirm={() => void handleDeleteConfirm()}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </ProtectedLayout>
  );
}

/* ─── 辅助组件 ─── */

function StatItem({
  label,
  value,
  risk,
}: {
  label: string;
  value: number | string;
  risk?: boolean;
}) {
  return (
    <div className="flex flex-col gap-xs">
      <span className="text-caption text-text-secondary">{label}</span>
      <span
        className={`text-data-secondary ${risk ? "state-risk" : ""}`}
        data-mono
      >
        {typeof value === "number" ? value.toLocaleString("zh-CN") : value}
      </span>
    </div>
  );
}

function DeleteConfirmDialog({
  item,
  deleting,
  onConfirm,
  onCancel,
}: {
  item: BacktestTask;
  deleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Dialog
      open
      onOpenChange={(open: boolean) => {
        if (!open) onCancel();
      }}
      title="确认删除"
      description={`确定要删除回测「${item.displayName || item.id.slice(0, 12)}」吗？此操作不可撤销。`}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel} disabled={deleting}>
            取消
          </Button>
          <Button variant="primary" loading={deleting} onClick={onConfirm}>
            确认删除
          </Button>
        </>
      }
    >
      <p className="text-body-secondary text-text-muted">
        删除后将无法恢复，请确认是否继续。
      </p>
    </Dialog>
  );
}

function fmtPct(val: number): string {
  if (!Number.isFinite(val)) return "0.00%";
  return `${(val * 100).toFixed(2)}%`;
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
