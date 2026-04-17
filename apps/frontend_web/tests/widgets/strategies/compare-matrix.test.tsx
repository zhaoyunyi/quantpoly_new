import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  CompareMatrix,
  type CompareMetricRow,
} from "../../../app/widgets/strategies/CompareMatrix";

const strategyNames = ["策略A", "策略B", "策略C"];

describe("CompareMatrix highlighting", () => {
  it("given_numeric_values_when_rendered_then_highlights_best_and_worst", () => {
    const metrics: CompareMetricRow[] = [
      { label: "年化收益率", values: ["12.5%", "8.3%", "15.1%"] },
    ];

    render(
      <CompareMatrix strategyNames={strategyNames} metrics={metrics} />,
    );

    // 15.1% is best (highest) → text-state-up font-medium
    const best = screen.getByText("15.1%");
    expect(best.className).toContain("text-state-up");
    expect(best.className).toContain("font-medium");

    // 8.3% is worst (lowest) → text-state-down
    const worst = screen.getByText("8.3%");
    expect(worst.className).toContain("text-state-down");

    // 12.5% is neither best nor worst → no highlight classes
    const mid = screen.getByText("12.5%");
    expect(mid.className).not.toContain("text-state-up");
    expect(mid.className).not.toContain("text-state-down");
  });

  it("given_drawdown_metric_when_rendered_then_reverses_highlight", () => {
    const metrics: CompareMetricRow[] = [
      { label: "最大回撤", values: ["20%", "10%", "35%"] },
    ];

    render(
      <CompareMatrix strategyNames={strategyNames} metrics={metrics} />,
    );

    // For drawdown, lower is better → 10% is best
    const best = screen.getByText("10%");
    expect(best.className).toContain("text-state-up");
    expect(best.className).toContain("font-medium");

    // 35% is worst (largest drawdown)
    const worst = screen.getByText("35%");
    expect(worst.className).toContain("text-state-down");
  });

  it("given_highlight_disabled_when_rendered_then_no_highlight_classes", () => {
    const metrics: CompareMetricRow[] = [
      { label: "年化收益率", values: ["12.5%", "8.3%", "15.1%"] },
    ];

    render(
      <CompareMatrix
        strategyNames={strategyNames}
        metrics={metrics}
        highlightBestWorst={false}
      />,
    );

    const best = screen.getByText("15.1%");
    expect(best.className).not.toContain("text-state-up");

    const worst = screen.getByText("8.3%");
    expect(worst.className).not.toContain("text-state-down");
  });

  it("given_localized_number_strings_when_rendered_then_ignores_thousand_separators", () => {
    const metrics: CompareMetricRow[] = [
      { label: "累计收益", values: ["1,234.5", "999.9", "10,000"] },
    ];

    render(
      <CompareMatrix strategyNames={strategyNames} metrics={metrics} />,
    );

    const best = screen.getByText("10,000");
    expect(best.className).toContain("text-state-up");
    expect(best.className).toContain("font-medium");

    const worst = screen.getByText("999.9");
    expect(worst.className).toContain("text-state-down");

    const mid = screen.getByText("1,234.5");
    expect(mid.className).not.toContain("text-state-up");
    expect(mid.className).not.toContain("text-state-down");
  });
});
