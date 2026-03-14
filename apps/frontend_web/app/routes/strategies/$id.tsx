/**
 * /strategies/$id — 策略详情/编辑页
 *
 * 功能：
 * - 策略详情展示
 * - 编辑保存（名称/参数）
 * - 状态变更（激活/停用/归档）
 * - 关联回测列表与统计
 * - 快捷创建回测
 * - 执行参数校验
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategy,
  getStrategyTemplates,
  updateStrategy,
  activateStrategy,
  deactivateStrategy,
  archiveStrategy,
  getStrategyBacktests,
  getStrategyBacktestStats,
  createBacktestForStrategy,
  validateExecution,
} from "@qp/api-client";
import type {
  StrategyItem,
  StrategyTemplate,
  StrategyBacktest,
  StrategyBacktestStats,
  AppError,
} from "@qp/api-client";
import { Button, Dialog, Skeleton, EmptyState, useToast } from "@qp/ui";
import { StrategyStatusBadge } from "../../widgets/strategies/StrategyStatusBadge";
import {
  StrategyForm,
  type StrategyFormData,
} from "../../widgets/strategies/StrategyForm";
import { BacktestInlineList } from "../../widgets/strategies/BacktestInlineList";

export const Route = createFileRoute("/strategies/$id")({
  component: StrategyDetailPage,
});

export function StrategyDetailPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const toast = useToast();

  /* ─── 策略数据 ─── */
  const [strategy, setStrategy] = useState<StrategyItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppError | null>(null);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);

  /* ─── 编辑模式 ─── */
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editFieldErrors, setEditFieldErrors] = useState<
    Record<string, string>
  >({});

  /* ─── 回测数据 ─── */
  const [backtests, setBacktests] = useState<StrategyBacktest[]>([]);
  const [backtestsLoading, setBacktestsLoading] = useState(true);
  const [btStats, setBtStats] = useState<StrategyBacktestStats | null>(null);
  const [creatingBacktest, setCreatingBacktest] = useState(false);

  /* ─── 校验对话框 ─── */
  const [validateOpen, setValidateOpen] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validateResult, setValidateResult] = useState<string | null>(null);

  const loadStrategy = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, tpls] = await Promise.all([
        getStrategy(id),
        getStrategyTemplates(),
      ]);
      setStrategy(s);
      setTemplates(tpls);
    } catch (err) {
      setError(err as AppError);
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadBacktests = useCallback(async () => {
    setBacktestsLoading(true);
    try {
      const [btResult, stats] = await Promise.all([
        getStrategyBacktests(id),
        getStrategyBacktestStats(id),
      ]);
      setBacktests(btResult.items);
      setBtStats(stats);
    } catch {
      // 回测加载失败不阻塞主页面
    } finally {
      setBacktestsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadStrategy();
    void loadBacktests();
  }, [loadStrategy, loadBacktests]);

  /* ─── 操作 ─── */
  const handleSave = async (data: StrategyFormData) => {
    setSaving(true);
    setEditFieldErrors({});
    try {
      const params: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(data.parameters)) {
        const num = Number(v);
        params[k] = Number.isNaN(num) ? v : num;
      }
      const updated = await updateStrategy(id, {
        name: data.name,
        parameters: params,
      });
      setStrategy(updated);
      setEditing(false);
      toast.show("策略已更新", "success");
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.kind === "validation") {
        const msg = appErr.message || "";
        const fieldMatch = msg.match(/parameter[:\s]+(\w+)/i);
        if (fieldMatch) {
          setEditFieldErrors({ [fieldMatch[1]]: msg });
        } else {
          setEditFieldErrors({ name: msg });
        }
      } else {
        toast.show(appErr.message || "更新失败", "error");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleStatusAction = async (
    action: "activate" | "deactivate" | "archive",
  ) => {
    const actionMap = {
      activate: activateStrategy,
      deactivate: deactivateStrategy,
      archive: archiveStrategy,
    };
    const labelMap = {
      activate: "已激活",
      deactivate: "已停用",
      archive: "已归档",
    };
    try {
      const updated = await actionMap[action](id);
      setStrategy(updated);
      toast.show(`策略${labelMap[action]}`, "success");
    } catch (err) {
      toast.show((err as AppError).message || "操作失败", "error");
    }
  };

  const handleCreateBacktest = async () => {
    setCreatingBacktest(true);
    try {
      await createBacktestForStrategy(id, { config: {} });
      toast.show("回测已创建", "success");
      void loadBacktests();
    } catch (err) {
      toast.show((err as AppError).message || "创建回测失败", "error");
    } finally {
      setCreatingBacktest(false);
    }
  };

  const handleValidateExecution = async () => {
    if (!strategy) return;
    setValidating(true);
    setValidateResult(null);
    try {
      const result = await validateExecution(id, {
        parameters: strategy.parameters as Record<string, unknown>,
      });
      setValidateResult(result.valid ? "参数校验通过 ✓" : "参数校验未通过");
    } catch (err) {
      setValidateResult((err as AppError).message || "校验失败");
    } finally {
      setValidating(false);
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

  if (error || !strategy) {
    return (
      <ProtectedLayout>
        <EmptyState
          title="策略不存在"
          description={error?.message || "未能加载策略详情"}
          action={
            <Button
              variant="secondary"
              onClick={() => void navigate({ to: "/strategies" })}
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
                onClick={() => void navigate({ to: "/strategies" })}
              >
                ← 策略列表
              </button>
            </div>
            <h1 className="text-title-page mt-xs">{strategy.name}</h1>
            <div className="flex items-center gap-sm mt-xs">
              <StrategyStatusBadge status={strategy.status} />
              <span className="text-caption text-text-muted">
                模板: {strategy.template}
              </span>
              <span className="text-data-mono text-text-muted">
                创建于 {formatDate(strategy.createdAt)}
              </span>
            </div>
          </div>
          <div className="shrink-0 flex gap-sm flex-wrap">
            {strategy.status !== "archived" && (
              <Button variant="secondary" onClick={() => setEditing(!editing)}>
                {editing ? "取消编辑" : "编辑"}
              </Button>
            )}
            {(strategy.status === "draft" ||
              strategy.status === "inactive") && (
              <Button onClick={() => void handleStatusAction("activate")}>
                激活
              </Button>
            )}
            {strategy.status === "active" && (
              <Button
                variant="secondary"
                onClick={() => void handleStatusAction("deactivate")}
              >
                停用
              </Button>
            )}
            {strategy.status !== "archived" && (
              <Button
                variant="ghost"
                onClick={() => void handleStatusAction("archive")}
              >
                归档
              </Button>
            )}
          </div>
        </header>

        {/* 编辑/只读表单 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">策略参数</h2>
          <StrategyForm
            templates={templates}
            initialValues={strategy}
            readonly={!editing}
            onSubmit={(data) => void handleSave(data)}
            loading={saving}
            fieldErrors={editFieldErrors}
          />
          {!editing && strategy.status !== "archived" && (
            <div className="flex gap-sm mt-md">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setValidateOpen(true);
                  void handleValidateExecution();
                }}
              >
                校验执行参数
              </Button>
            </div>
          )}
        </section>

        {/* 回测统计 */}
        {btStats && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">回测统计</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-md">
              <StatItem label="总回测" value={btStats.totalCount} />
              <StatItem label="已完成" value={btStats.completedCount} />
              <StatItem label="运行中" value={btStats.runningCount} />
              <StatItem
                label="平均收益率"
                value={fmtPct(btStats.averageReturnRate)}
              />
              <StatItem
                label="平均最大回撤"
                value={fmtPct(btStats.averageMaxDrawdown)}
                risk={btStats.averageMaxDrawdown > 0.2}
              />
            </div>
          </section>
        )}

        {/* 关联回测 */}
        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <BacktestInlineList
            items={backtests}
            loading={backtestsLoading}
            onCreateBacktest={
              creatingBacktest ? undefined : () => void handleCreateBacktest()
            }
          />
        </section>

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>

      {/* 校验结果对话框 */}
      <Dialog
        open={validateOpen}
        onOpenChange={setValidateOpen}
        title="执行参数校验"
      >
        {validating ? (
          <Skeleton width="100%" height="40px" />
        ) : (
          <p className="text-body">{validateResult}</p>
        )}
      </Dialog>
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

function formatDate(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

function fmtPct(val: number): string {
  if (!Number.isFinite(val)) return "0.00%";
  return `${(val * 100).toFixed(2)}%`;
}
