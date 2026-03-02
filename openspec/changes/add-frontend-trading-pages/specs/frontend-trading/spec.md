## ADDED Requirements

### Requirement: Frontend SHALL provide trading account management and order execution UI

前端 SHALL 提供交易账户与下单能力，并对接后端 `trading-account` 公开端点。

#### Scenario: Place a buy order via command endpoint
- **GIVEN** 用户已登录且拥有交易账户
- **WHEN** 用户在 `/trading` 提交买入指令
- **THEN** 前端调用 `POST /trading/accounts/{id}/buy`
- **AND** 成功后刷新账户 summary/positions/orders

