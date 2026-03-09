## 1. 路由与页面

- [x] 1.1 新增 `/dashboard` 路由（受保护）
- [x] 1.2 页面结构遵循“结论优先”：顶部 KPI cards + 次级列表/图表区域 + 免责声明

## 2. 数据对接（并行可做）

- [x] 2.1 接入 `GET /monitor/summary`（运营摘要：accounts/strategies/backtests/tasks/signals/alerts）
- [x] 2.2 接入 `GET /trading/accounts/aggregate`（资产汇总：若后端返回结构变化，以 envelope 解包为准）
- [x] 2.3 接入 `GET /backtests/statistics`
- [x] 2.4 （可选）接入 `GET /risk/alerts/stats`、`GET /signals/dashboard`

## 3. 组件规划

- [x] 3.1 `KpiCard`（标题/主数字/次数字/状态色）
- [x] 3.2 `StatusPill`（running/failed/ok）
- [x] 3.3 `DegradedBanner`（当 summary.degraded.enabled=true 提示降级原因）
- [x] 3.4 `QuickActions`（跳转策略/回测/交易/监控）

## 4. 状态与错误

- [x] 4.1 加载态 Skeleton（首屏）
- [x] 4.2 单端点失败不阻断整页（局部错误卡片 + 重试）

## 5. 测试（TDD）

- [x] 5.1 单元测试：summary.degraded.enabled 时展示降级提示
- [x] 5.2 单元测试：401 时触发 AuthGuard 重定向

## 6. 回归验证

- [x] 6.1 `cd apps/frontend_web && npm run build`
- [x] 6.2 `pytest -q`
