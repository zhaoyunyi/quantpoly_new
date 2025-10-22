"""
tests/frontend/test_backtest_center_routes.py

验证前端回测中心路由文件与路由注册是否就位。
"""

from __future__ import annotations

import json
from pathlib import Path


def test_backtest_routes_exist() -> None:
    """回测中心页面文件存在。"""
    routes_dir = Path("apps/frontend_web/app/routes/backtests")
    assert routes_dir.is_dir(), "缺少 routes/backtests/ 目录"

    index_file = routes_dir / "index.tsx"
    assert index_file.exists(), "缺少 /backtests 列表页路由文件"

    detail_file = routes_dir / "$id.tsx"
    assert detail_file.exists(), "缺少 /backtests/$id 详情页路由文件"


def test_backtest_widgets_exist() -> None:
    """回测 Widget 组件文件存在。"""
    widgets_dir = Path("apps/frontend_web/app/widgets/backtests")
    assert widgets_dir.is_dir(), "缺少 widgets/backtests/ 目录"

    expected_widgets = [
        "BacktestStatusBadge.tsx",
        "BacktestTable.tsx",
        "BacktestCreateDialog.tsx",
        "BacktestResultPanel.tsx",
        "BacktestActions.tsx",
    ]
    for widget_name in expected_widgets:
        assert (widgets_dir / widget_name).exists(), f"缺少 widget: {widget_name}"


def test_backtest_routes_registered_in_route_tree() -> None:
    """回测路由已注册到 routeTree.gen.ts。"""
    route_tree_path = Path("apps/frontend_web/app/routeTree.gen.ts")
    content = route_tree_path.read_text(encoding="utf-8")

    assert "/backtests/" in content, "routeTree 缺少 /backtests/ 路由注册"
    assert "/backtests/$id" in content, "routeTree 缺少 /backtests/$id 路由注册"


def test_api_client_exports_backtest_endpoints() -> None:
    """API client 包含回测相关 endpoint 函数。"""
    endpoints_path = Path("libs/frontend_api_client/src/endpoints.ts")
    content = endpoints_path.read_text(encoding="utf-8")

    expected_functions = [
        "getBacktests",
        "getBacktest",
        "createBacktest",
        "getBacktestResult",
        "getRelatedBacktests",
        "renameBacktest",
        "cancelBacktest",
        "retryBacktest",
        "deleteBacktest",
        "compareBacktests",
        "getBacktestStatistics",
    ]
    for fn_name in expected_functions:
        assert f"function {fn_name}" in content, f"API client 缺少 endpoint: {fn_name}"
