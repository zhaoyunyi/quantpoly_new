/**
 * App Shell 导航契约测试
 *
 * 目标：确保“风控中心”导航不会指向不存在的前端页面。
 */

import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "@qp/shell";

describe("app_shell_navigation", () => {
  it("given_risk_nav_item_when_resolve_path_then_points_to_trading_analytics", () => {
    const riskItem = NAV_ITEMS.find((item) => item.label === "风控中心");

    expect(riskItem).toBeDefined();
    expect(riskItem?.path).toBe("/trading/analytics");
  });
});
