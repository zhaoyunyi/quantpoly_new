import type { StrategyHealthReport, OverfitRisk } from "@qp/api-client";
import { formatPercent, formatInt, formatDate } from "../../shared/format";

function scoreColor(score: number): string {
  if (score >= 80) return "text-primary-600";
  if (score >= 60) return "text-yellow-600";
  if (score >= 40) return "text-orange-500";
  return "text-state-risk";
}

function scoreBg(score: number): string {
  if (score >= 80) return "bg-primary-500/10";
  if (score >= 60) return "bg-yellow-500/10";
  if (score >= 40) return "bg-orange-500/10";
  return "bg-red-500/10";
}

const RISK_STYLES: Record<OverfitRisk, string> = {
  LOW: "bg-primary-500/10 text-primary-700",
  MEDIUM: "bg-yellow-500/10 text-yellow-700",
  HIGH: "bg-orange-500/10 text-orange-700",
  CRITICAL: "bg-red-500/10 text-state-risk",
};

const RISK_LABELS: Record<OverfitRisk, string> = {
  LOW: "低风险",
  MEDIUM: "中等风险",
  HIGH: "高风险",
  CRITICAL: "极高风险",
};

function isCompletedReport(
  report: StrategyHealthReport,
): report is StrategyHealthReport &
  Required<
    Pick<
      StrategyHealthReport,
      | "overallScore"
      | "overfitRisk"
      | "inSampleReturn"
      | "outSampleReturn"
      | "returnRatio"
      | "paramSensitivity"
      | "tradeCount"
      | "maxDrawdown"
      | "sharpeRatio"
      | "warnings"
    >
  > {
  return (
    report.status === "completed" &&
    typeof report.overallScore === "number" &&
    typeof report.returnRatio === "number" &&
    typeof report.sharpeRatio === "number" &&
    typeof report.inSampleReturn === "number" &&
    typeof report.outSampleReturn === "number" &&
    typeof report.tradeCount === "number" &&
    typeof report.maxDrawdown === "number" &&
    report.overfitRisk !== undefined &&
    report.paramSensitivity !== undefined &&
    report.warnings !== undefined
  );
}

export function HealthReportCard({ report }: { report: StrategyHealthReport }) {
  if (!isCompletedReport(report)) {
    const isFailed = report.status === "failed";

    return (
      <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg flex flex-col gap-md">
        <div className="flex items-center justify-between">
          <h3 className="text-title-section">
            {isFailed ? "报告执行失败" : "报告尚未完成"}
          </h3>
          <span className="text-caption text-text-muted">
            {formatDate(report.createdAt)}
          </span>
        </div>
        <div className="rounded-md border border-secondary-300/20 bg-bg-subtle p-md">
          <p className="text-body font-medium">
            当前状态：{report.status}
          </p>
          <p className="text-body-secondary mt-xs">
            {report.error ?? "报告仍在生成中，请稍后刷新查看。"}
          </p>
        </div>
      </div>
    );
  }

  const paramEntries = Object.entries(report.paramSensitivity);

  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg flex flex-col gap-md">
      <div className="flex items-center justify-between">
        <h3 className="text-title-section">健康报告</h3>
        <span className="text-caption text-text-muted">
          {formatDate(report.createdAt)}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md">
        <div className={`rounded-md p-md flex flex-col items-center ${scoreBg(report.overallScore)}`}>
          <span className="text-caption text-text-secondary">综合评分</span>
          <span className={`text-2xl font-bold ${scoreColor(report.overallScore)}`}>
            {report.overallScore}
          </span>
        </div>
        <div className="rounded-md p-md flex flex-col items-center bg-bg-subtle">
          <span className="text-caption text-text-secondary">过拟合风险</span>
          <span className={`mt-xs px-2 py-0.5 rounded-sm text-caption font-medium ${RISK_STYLES[report.overfitRisk]}`}>
            {RISK_LABELS[report.overfitRisk]}
          </span>
        </div>
        <div className="rounded-md p-md flex flex-col items-center bg-bg-subtle">
          <span className="text-caption text-text-secondary">收益比</span>
          <span className="text-data-secondary">{report.returnRatio.toFixed(2)}</span>
        </div>
        <div className="rounded-md p-md flex flex-col items-center bg-bg-subtle">
          <span className="text-caption text-text-secondary">夏普比率</span>
          <span className="text-data-secondary">{report.sharpeRatio.toFixed(2)}</span>
        </div>
      </div>

      <div>
        <h4 className="text-body font-medium mb-sm">样本收益对比</h4>
        <table className="w-full text-body">
          <thead>
            <tr className="border-b border-secondary-300/20">
              <th className="text-left py-xs text-caption text-text-secondary">指标</th>
              <th className="text-right py-xs text-caption text-text-secondary">值</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-secondary-300/10">
              <td className="py-xs">样本内收益</td>
              <td className="text-right text-data-mono">{formatPercent(report.inSampleReturn)}</td>
            </tr>
            <tr className="border-b border-secondary-300/10">
              <td className="py-xs">样本外收益</td>
              <td className="text-right text-data-mono">{formatPercent(report.outSampleReturn)}</td>
            </tr>
            <tr>
              <td className="py-xs">收益比 (外/内)</td>
              <td className="text-right text-data-mono">{report.returnRatio.toFixed(4)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {paramEntries.length > 0 && (
        <div>
          <h4 className="text-body font-medium mb-sm">参数敏感性分析</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-body">
              <thead>
                <tr className="border-b border-secondary-300/20">
                  <th className="text-left py-xs text-caption text-text-secondary">参数</th>
                  <th className="text-left py-xs text-caption text-text-secondary">评级</th>
                  <th className="text-right py-xs text-caption text-text-secondary">原始值</th>
                  <th className="text-left py-xs text-caption text-text-secondary">扰动结果</th>
                </tr>
              </thead>
              <tbody>
                {paramEntries.map(([name, sensitivity]) => (
                  <tr key={name} className="border-b border-secondary-300/10">
                    <td className="py-xs font-medium">{name}</td>
                    <td className="py-xs">{sensitivity.rating}</td>
                    <td className="text-right py-xs text-data-mono">{sensitivity.originalValue}</td>
                    <td className="py-xs">
                      <div className="flex flex-wrap gap-xs">
                        {sensitivity.variations.map((v, i) => (
                          <span key={i} className="text-caption text-text-muted">
                            {v.perturbation}: {v.changePercent >= 0 ? "+" : ""}{v.changePercent.toFixed(1)}%
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div>
        <h4 className="text-body font-medium mb-sm">交易统计</h4>
        <div className="grid grid-cols-3 gap-md">
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-secondary">交易次数</span>
            <span className="text-data-secondary">{formatInt(report.tradeCount)}</span>
          </div>
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-secondary">最大回撤</span>
            <span className="text-data-secondary state-risk">{formatPercent(report.maxDrawdown)}</span>
          </div>
          <div className="flex flex-col gap-xs">
            <span className="text-caption text-text-secondary">夏普比率</span>
            <span className="text-data-secondary">{report.sharpeRatio.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {report.warnings.length > 0 && (
        <div className="rounded-md bg-orange-500/5 border border-orange-500/20 p-md">
          <h4 className="text-body font-medium text-orange-700 mb-xs">风险警告</h4>
          <ul className="list-disc list-inside text-caption text-orange-700 space-y-xs">
            {report.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
