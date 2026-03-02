## 1. `/trading` 交易主页面

- [ ] 1.1 账户列表：`GET /trading/accounts`
- [ ] 1.2 账户概览：`GET /trading/accounts/{id}/summary`
- [ ] 1.3 持仓：`GET /trading/accounts/{id}/positions`
- [ ] 1.4 订单：`GET /trading/accounts/{id}/orders`
- [ ] 1.5 买入/卖出指令：
  - [ ] `POST /trading/accounts/{id}/buy`
  - [ ] `POST /trading/accounts/{id}/sell`
  - [ ] 处理冲突：`INSUFFICIENT_FUNDS`、`INSUFFICIENT_POSITION`

## 2. `/trading/accounts` 账户管理页

- [ ] 2.1 创建账户：`POST /trading/accounts`（accountName/initialCapital）
- [ ] 2.2 更新账户：`PUT /trading/accounts/{id}`（name/isActive）
- [ ] 2.3 过滤配置：`GET /trading/accounts/filter-config`
- [ ] 2.4 汇总：`GET /trading/accounts/aggregate`

## 3. `/trading/analytics` 分析页

- [ ] 3.1 风险指标：`GET /trading/accounts/{id}/risk-metrics`
- [ ] 3.2 资金曲线：`GET /trading/accounts/{id}/equity-curve`
- [ ] 3.3 交易统计：`GET /trading/accounts/{id}/trade-stats`
- [ ] 3.4 资金流水：`GET /trading/accounts/{id}/cash-flows`
- [ ] 3.5 风险评估：
  - [ ] `GET /trading/accounts/{id}/risk-assessment`
  - [ ] `POST /trading/accounts/{id}/risk-assessment/evaluate`
  - [ ] 处理 202 `RISK_ASSESSMENT_PENDING`

## 4. 组件规划

- [ ] 4.1 `AccountSelector`
- [ ] 4.2 `AccountSummaryCards`
- [ ] 4.3 `PositionsTable`
- [ ] 4.4 `OrderTicket`（buy/sell 表单）
- [ ] 4.5 `OrdersTable`
- [ ] 4.6 `CashFlowTable`
- [ ] 4.7 `EquityCurveChart`（可先占位，后续引入图表库）

## 5. 测试（TDD）

- [ ] 5.1 单元测试：buy/sell 冲突错误码映射与提示
- [ ] 5.2 单元测试：risk assessment pending 分支

## 6. 回归验证

- [ ] 6.1 `cd apps/frontend_web && npm run build`
- [ ] 6.2 `pytest -q`

