# Change: 前端交易账户与交易执行（Trading）页面

## Why

交易页面需要对接后端 `trading-account` 能力，提供账户管理、持仓与订单、买卖指令、资金流水与分析视图，并与风控快照/评估接口联动。

## What Changes

- 实现路由：
  - `/trading`（交易主控：选择账户、查看概览、下单）
  - `/trading/accounts`（账户管理）
  - `/trading/analytics`（风险/绩效/曲线/历史）
- 对接后端端点（节选）：
  - `GET/POST /trading/accounts`、`PUT /trading/accounts/{id}`
  - `GET /trading/accounts/{id}/summary`、`GET /trading/accounts/{id}/positions`
  - `POST /trading/accounts/{id}/buy`、`POST /trading/accounts/{id}/sell`
  - `GET/POST/PATCH/DELETE /trading/accounts/{id}/orders*`
  - `GET /trading/accounts/{id}/cash-flows*`
  - `POST /trading/accounts/{id}/deposit`、`POST /trading/accounts/{id}/withdraw`
  - `GET/POST /trading/accounts/{id}/risk-assessment*`

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/trading/*`
  - `libs/frontend_api_client/*`
- Affected specs:
  - `frontend-trading`

