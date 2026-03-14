/**
 * /strategies — 策略列表页
 *
 * 功能：
 * - 搜索、筛选（status/template）、分页
 * - 行操作：查看/编辑/激活/停用/归档/删除
 * - 创建策略（从模板下拉选择 + 填写名称参数）
 * - 删除保护（二次确认 Dialog + 409 STRATEGY_IN_USE 提示）
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategies,
  getStrategyTemplates,
  createStrategy,
  activateStrategy,
  deactivateStrategy,
  archiveStrategy,
  deleteStrategy,
} from "@qp/api-client";
import type {
  StrategyItem,
  StrategyListResult,
  StrategyTemplate,
  AppError,
} from "@qp/api-client";
import {
  Button,
  TextField,
  Select,
  Dialog,
  Skeleton,
  EmptyState,
  useToast,
} from "@qp/ui";
import { StrategyTable } from "../../widgets/strategies/StrategyTable";
import {
  StrategyForm,
  type StrategyFormData,
} from "../../widgets/strategies/StrategyForm";
import { Pagination } from "../../widgets/strategies/Pagination";

export const Route = createFileRoute("/strategies/")({
  component: StrategiesListPage,
});

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 300;

const STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "draft", label: "草稿" },
  { value: "active", label: "运行中" },
  { value: "inactive", label: "已停用" },
  { value: "archived", label: "已归档" },
];

export function StrategiesListPage() {
  const navigate = useNavigate();
  const toast = useToast();

  /* ─── 列表状态 ─── */
  const [items, setItems] = useState<StrategyItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppError | null>(null);

  /* ─── 筛选/搜索 ─── */
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );

  /* ─── 创建对话框 ─── */
  const [createOpen, setCreateOpen] = useState(false);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [creating, setCreating] = useState(false);
  const [createFieldErrors, setCreateFieldErrors] = useState<
    Record<string, string>
  >({});

  /* ─── 删除确认 ─── */
  const [deleteTarget, setDeleteTarget] = useState<StrategyItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  /* ─── 数据加载 ─── */
  const loadList = useCallback(async (p: number, s: string, status: string) => {
    setLoading(true);
    setError(null);
    try {
      const result: StrategyListResult = await getStrategies({
        page: p,
        pageSize: PAGE_SIZE,
        search: s || undefined,
        status: status || undefined,
      });
      setItems(result.items);
      setTotal(result.total);
      setPage(result.page);
    } catch (err) {
      setError(err as AppError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadList(page, search, statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearchChange = (val: string) => {
    setSearch(val);
    clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      void loadList(1, val, statusFilter);
    }, DEBOUNCE_MS);
  };

  const handleStatusChange = (val: string) => {
    setStatusFilter(val);
    void loadList(1, search, val);
  };

  const handlePageChange = (p: number) => {
    void loadList(p, search, statusFilter);
  };

  const reload = () => void loadList(page, search, statusFilter);

  /* ─── 行操作 ─── */
  const handleView = (id: string) =>
    void navigate({ to: "/strategies/$id", params: { id } });
  const handleEdit = (id: string) =>
    void navigate({ to: "/strategies/$id", params: { id } });

  const handleActivate = async (id: string) => {
    try {
      await activateStrategy(id);
      toast.show("策略已激活", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "激活失败", "error");
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await deactivateStrategy(id);
      toast.show("策略已停用", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "停用失败", "error");
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await archiveStrategy(id);
      toast.show("策略已归档", "success");
      reload();
    } catch (err) {
      toast.show((err as AppError).message || "归档失败", "error");
    }
  };

  const handleDeleteRequest = (id: string) => {
    const item = items.find((i) => i.id === id);
    if (item) {
      setDeleteTarget(item);
      setDeleteError(null);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteStrategy(deleteTarget.id);
      toast.show("策略已删除", "success");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.code === "STRATEGY_IN_USE") {
        setDeleteError(
          "该策略有正在运行或排队中的回测任务，无法删除。请先取消相关回测。",
        );
      } else {
        setDeleteError(appErr.message || "删除失败");
      }
    } finally {
      setDeleting(false);
    }
  };

  /* ─── 创建策略 ─── */
  const handleOpenCreate = async () => {
    setCreateOpen(true);
    setCreateFieldErrors({});
    try {
      const tpls = await getStrategyTemplates();
      setTemplates(tpls);
    } catch {
      toast.show("加载模板失败", "error");
    }
  };

  const handleCreate = async (data: StrategyFormData) => {
    setCreating(true);
    setCreateFieldErrors({});
    try {
      const params: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(data.parameters)) {
        const num = Number(v);
        params[k] = Number.isNaN(num) ? v : num;
      }
      await createStrategy({
        name: data.name,
        template: data.template,
        parameters: params,
      });
      toast.show("策略创建成功", "success");
      setCreateOpen(false);
      reload();
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.kind === "validation") {
        // 将后端 422 错误映射到字段
        const msg = appErr.message || "";
        const fieldMatch = msg.match(/parameter[:\s]+(\w+)/i);
        if (fieldMatch) {
          setCreateFieldErrors({ [fieldMatch[1]]: msg });
        } else {
          setCreateFieldErrors({ name: msg });
        }
      } else {
        toast.show(appErr.message || "创建失败", "error");
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        {/* 页面标题 */}
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <h1 className="text-title-page">策略管理</h1>
            <p className="text-body-secondary mt-xs">
              管理您的量化策略，支持创建、编辑、激活/停用、归档与删除。
            </p>
          </div>
          <div className="shrink-0 flex gap-sm">
            <Button
              variant="secondary"
              onClick={() => void navigate({ to: "/strategies/simple" })}
            >
              向导创建
            </Button>
            <Button onClick={() => void handleOpenCreate()}>创建策略</Button>
          </div>
        </header>

        {/* 搜索和筛选 */}
        <div className="flex items-end gap-md flex-wrap">
          <TextField
            label="搜索"
            placeholder="输入策略名称搜索…"
            value={search}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              handleSearchChange(e.target.value)
            }
            size="sm"
            className="w-64"
            startAdornment={
              <svg
                width="14"
                height="14"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  cx="7"
                  cy="7"
                  r="5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M11 11l3.5 3.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            }
          />
          <Select
            label="状态"
            options={STATUS_OPTIONS}
            value={statusFilter}
            onValueChange={handleStatusChange}
            className="w-40"
          />
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
            description={error.message || "无法获取策略列表"}
            action={
              <Button variant="secondary" onClick={reload}>
                重试
              </Button>
            }
          />
        ) : (
          <>
            <StrategyTable
              items={items}
              loading={loading}
              onView={handleView}
              onEdit={handleEdit}
              onActivate={(id) => void handleActivate(id)}
              onDeactivate={(id) => void handleDeactivate(id)}
              onArchive={(id) => void handleArchive(id)}
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

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>

      {/* 创建策略对话框 */}
      <Dialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="创建策略"
        description="选择模板并配置参数以创建新策略。"
      >
        <StrategyForm
          templates={templates}
          onSubmit={(data) => void handleCreate(data)}
          loading={creating}
          fieldErrors={createFieldErrors}
        />
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title="确认删除"
        description={`确定要删除策略「${deleteTarget?.name ?? ""}」吗？此操作不可撤销。`}
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={deleting}
            >
              取消
            </Button>
            <Button
              variant="primary"
              loading={deleting}
              onClick={() => void handleDeleteConfirm()}
            >
              确认删除
            </Button>
          </>
        }
      >
        {deleteError && (
          <p className="text-body text-state-risk" role="alert">
            {deleteError}
          </p>
        )}
      </Dialog>
    </ProtectedLayout>
  );
}
