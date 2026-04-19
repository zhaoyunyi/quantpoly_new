import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState, type ChangeEvent } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategyTemplates,
  createStrategyHealthReport,
  getStrategyHealthReports,
} from "@qp/api-client";
import type {
  StrategyTemplate,
  StrategyHealthReport,
  HealthReportListResult,
  AppError,
} from "@qp/api-client";
import { Button, TextField, Select, Skeleton, EmptyState, useToast } from "@qp/ui";
import { HealthReportCard } from "../../widgets/strategies/HealthReportCard";
import { formatDate } from "../../shared/format";

export const Route = createFileRoute("/strategies/health")({
  component: StrategyHealthPage,
});

const PAGE_SIZE = 10;
const HEALTH_SUPPORTED_TEMPLATE_IDS = new Set(["moving_average", "mean_reversion"]);

function scoreColor(score: number): string {
  if (score >= 80) return "text-primary-600";
  if (score >= 60) return "text-yellow-600";
  if (score >= 40) return "text-orange-500";
  return "text-state-risk";
}

function hasNumericMetric(value: number | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function riskLabel(report: StrategyHealthReport): string {
  if (report.overfitRisk) return report.overfitRisk;
  if (report.status === "failed") return "FAILED";
  if (report.status === "running") return "RUNNING";
  if (report.status === "pending") return "PENDING";
  return "—";
}

export function StrategyHealthPage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);

  const [template, setTemplate] = useState("");
  const [symbol, setSymbol] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [initialCapital, setInitialCapital] = useState("");
  const [params, setParams] = useState<Record<string, string>>({});

  const [submitting, setSubmitting] = useState(false);
  const [currentReport, setCurrentReport] = useState<StrategyHealthReport | null>(null);

  const [reports, setReports] = useState<StrategyHealthReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsTotal, setReportsTotal] = useState(0);
  const [reportsPage, setReportsPage] = useState(1);

  const selectedTemplate = templates.find((t) => t.templateId === template);

  const loadTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const tpls = await getStrategyTemplates();
      setTemplates(
        tpls.filter((tpl) => HEALTH_SUPPORTED_TEMPLATE_IDS.has(tpl.templateId)),
      );
    } catch {
      toast.show("加载模板失败", "error");
    } finally {
      setTemplatesLoading(false);
    }
  }, [toast]);

  const loadReports = useCallback(async (page: number) => {
    setReportsLoading(true);
    try {
      const result: HealthReportListResult = await getStrategyHealthReports({
        page,
        pageSize: PAGE_SIZE,
      });
      setReports(result.items);
      setReportsTotal(result.total);
      setReportsPage(result.page);
    } catch {
      // silent
    } finally {
      setReportsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTemplates();
    void loadReports(1);
  }, [loadTemplates, loadReports]);

  useEffect(() => {
    if (!selectedTemplate) {
      setParams({});
      return;
    }
    const defaults: Record<string, string> = {};
    for (const key of Object.keys(selectedTemplate.requiredParameters)) {
      const def = selectedTemplate.defaults[key];
      defaults[key] = def !== undefined ? String(def) : "";
    }
    setParams(defaults);
  }, [template, selectedTemplate]);

  const handleParamChange = (key: string, value: string) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };
  const canSubmit =
    Boolean(selectedTemplate) && symbol.trim() && startDate && endDate && !submitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      const parameters: Record<string, number> = {};
      for (const [k, v] of Object.entries(params)) {
        const num = Number(v);
        if (Number.isNaN(num)) {
          toast.show(`参数 ${k} 必须为数字`, "error");
          setSubmitting(false);
          return;
        }
        parameters[k] = num;
      }
      const report = await createStrategyHealthReport({
        template,
        parameters,
        symbol: symbol.trim(),
        startDate,
        endDate,
        initialCapital: initialCapital ? Number(initialCapital) : undefined,
      });
      setCurrentReport(report);
      toast.show("健康报告生成成功", "success");
      void loadReports(1);
    } catch (err) {
      toast.show((err as AppError).message || "生成报告失败", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const templateOptions = [
    { value: "", label: "请选择模板" },
    ...templates.map((t) => ({ value: t.templateId, label: t.name })),
  ];

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg">
        <header className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-sm">
              <button
                type="button"
                className="text-primary-500 hover:text-primary-700 text-body transition-all duration-120 ease-out"
                onClick={() => void navigate({ to: "/strategies" })}
              >
                ← 策略管理
              </button>
            </div>
            <h1 className="text-title-page mt-xs">策略健康报告</h1>
            <p className="text-body-secondary mt-xs">
              分析策略的过拟合风险、参数敏感性与样本外表现。
            </p>
          </div>
        </header>

        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">配置分析参数</h2>
          {templatesLoading ? (
            <Skeleton width="100%" height="120px" />
          ) : (
            <div className="flex flex-col gap-md">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
                <Select
                  label="策略模板"
                  options={templateOptions}
                  value={template}
                  onValueChange={setTemplate}
                />
                <TextField
                  label="交易标的"
                  placeholder="如 AAPL、BTC-USD"
                  value={symbol}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setSymbol(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-md">
                <TextField
                  label="开始日期"
                  type="date"
                  value={startDate}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setStartDate(e.target.value)}
                />
                <TextField
                  label="结束日期"
                  type="date"
                  value={endDate}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEndDate(e.target.value)}
                />
                <TextField
                  label="初始资金（可选）"
                  type="number"
                  placeholder="100000"
                  value={initialCapital}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setInitialCapital(e.target.value)}
                />
              </div>
              {selectedTemplate && Object.keys(selectedTemplate.requiredParameters).length > 0 && (
                <div>
                  <h3 className="text-body font-medium mb-sm">策略参数</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-md">
                    {Object.entries(selectedTemplate.requiredParameters).map(([key, spec]) => (
                      <TextField
                        key={key}
                        label={key}
                        type="number"
                        placeholder={spec.min !== undefined ? `${spec.min} - ${spec.max}` : ""}
                        value={params[key] ?? ""}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => handleParamChange(key, e.target.value)}
                      />
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-end">
                <Button
                  onClick={() => void handleSubmit()}
                  loading={submitting}
                  disabled={!canSubmit}
                >
                  生成健康报告
                </Button>
              </div>
            </div>
          )}
        </section>

        {currentReport && <HealthReportCard report={currentReport} />}

        <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
          <h2 className="text-title-section mb-md">历史报告</h2>
          {reportsLoading ? (
            <div className="flex flex-col gap-sm">
              {Array.from({ length: 3 }).map((_, idx) => (
                <Skeleton key={idx} width="100%" height="48px" />
              ))}
            </div>
          ) : reports.length === 0 ? (
            <EmptyState title="暂无报告" description="提交分析后，历史报告将在此展示。" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body">
                <thead>
                  <tr className="border-b border-secondary-300/20">
                    <th className="text-left py-sm text-caption text-text-secondary">报告ID</th>
                    <th className="text-right py-sm text-caption text-text-secondary">评分</th>
                    <th className="text-left py-sm text-caption text-text-secondary">过拟合风险</th>
                    <th className="text-right py-sm text-caption text-text-secondary">夏普比率</th>
                    <th className="text-left py-sm text-caption text-text-secondary">创建时间</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr
                      key={r.reportId}
                      className="border-b border-secondary-300/10 hover:bg-bg-subtle cursor-pointer transition-colors"
                      onClick={() => setCurrentReport(r)}
                    >
                      <td className="py-sm text-data-mono">{r.reportId.slice(0, 8)}</td>
                      <td
                        className={`text-right py-sm font-medium ${
                          hasNumericMetric(r.overallScore)
                            ? scoreColor(r.overallScore)
                            : "text-text-muted"
                        }`}
                      >
                        {hasNumericMetric(r.overallScore) ? r.overallScore : "—"}
                      </td>
                      <td className="py-sm">{riskLabel(r)}</td>
                      <td className="text-right py-sm text-data-mono">
                        {hasNumericMetric(r.sharpeRatio) ? r.sharpeRatio.toFixed(2) : "—"}
                      </td>
                      <td className="py-sm text-text-muted">{formatDate(r.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {reportsTotal > PAGE_SIZE && (
                <div className="flex justify-center gap-sm mt-md">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={reportsPage <= 1}
                    onClick={() => void loadReports(reportsPage - 1)}
                  >
                    上一页
                  </Button>
                  <span className="text-caption text-text-muted self-center">
                    {reportsPage} / {Math.ceil(reportsTotal / PAGE_SIZE)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={reportsPage >= Math.ceil(reportsTotal / PAGE_SIZE)}
                    onClick={() => void loadReports(reportsPage + 1)}
                  >
                    下一页
                  </Button>
                </div>
              )}
            </div>
          )}
        </section>

        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  );
}
