## 1. `/trading` 交易主页面

- [x] 1.1 账户列表：`GET /trading/accounts`
- [x] 1.2 账户概览：`GET /trading/accounts/{id}/overview`
- [x] 1.3 持仓：`GET /trading/accounts/{id}/positions`
- [x] 1.4 订单：`GET /trading/accounts/{id}/orders`
- [x] 1.5 买入/卖出指令：
  - [x] `POST /trading/accounts/{id}/buy`
  - [x] `POST /trading/accounts/{id}/sell`
  - [x] 处理冲突：`INSUFFICIENT_FUNDS`、`INSUFFICIENT_POSITION`

## 2. `/trading/accounts` 账户管理页

- [x] 2.1 创建账户：`POST /trading/accounts`（accountName/initialCapital）
- [x] 2.2 更新账户：`PUT /trading/accounts/{id}`（name/isActive）
- [x] 2.3 过滤配置：`GET /trading/accounts/filter-config`
- [x] 2.4 汇总：`GET /trading/accounts/aggregate`

## 3. `/trading/analytics` 分析页

- [x] 3.1 风险指标：`GET /trading/accounts/{id}/risk-metrics`
- [x] 3.2 资金曲线：`GET /trading/accounts/{id}/equity-curve`
- [x] 3.3 交易统计：`GET /trading/accounts/{id}/trade-stats`
- [x] 3.4 资金流水：`GET /trading/accounts/{id}/cash-flows`
- [x] 3.5 风险评估：
  - [x] `GET /trading/accounts/{id}/risk-assessment`
  - [x] `POST /trading/accounts/{id}/risk-assessment/evaluate`
  - [x] 处理 202 `RISK_ASSESSMENT_PENDING`

## 4. 组件规划

- [x] 4.1 `AccountSelector`
- [x] 4.2 `AccountSummaryCards`
- [x] 4.3 `PositionsTable`
- [x] 4.4 `OrderTicket`（buy/sell 表单）
- [x] 4.5 `OrdersTable`
- [x] 4.6 `CashFlowTable`
- [x] 4.7 `EquityCurveChart`（可先占位，后续引入图表库）

## 5. 测试（TDD）

- [x] 5.1 单元测试：buy/sell 冲突错误码映射与提示
- [x] 5.2 单元测试：risk assessment pending 分支
- [x] 5.3 E2E（Playwright）：`/trading` buy/sell error mapping
- [x] 5.4 E2E（Playwright）：`/trading/accounts` 可创建账户
- [x] 5.5 E2E（Playwright）：`/trading/analytics` pending → evaluate
- [x] 5.6 联调契约（后端 composition root）：端点字段与错误码满足前端需求（pytest）

## 6. 回归验证

- [x] 6.1 `cd apps/frontend_web && npm run build`
- [x] 6.2 `pytest -q`
- [x] 6.3 `cd apps/frontend_web && npm test`
- [x] 6.4 `cd apps/frontend_web && npm run test:e2e`
