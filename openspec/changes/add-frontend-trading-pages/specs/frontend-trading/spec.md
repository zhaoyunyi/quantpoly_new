## ADDED Requirements

### Requirement: Frontend SHALL provide trading account management and order execution UI

前端 SHALL 提供交易账户与下单能力，并对接后端 `trading-account` 公开端点。

#### Scenario: Place a buy order via command endpoint
- **GIVEN** 用户已登录且拥有交易账户
- **WHEN** 用户在 `/trading` 提交买入指令
- **THEN** 前端调用 `POST /trading/accounts/{id}/buy`
- **AND** 成功后刷新账户 overview/positions/orders

#### Scenario: Show mapped error when buy order is rejected by insufficient funds
- **GIVEN** 用户已登录且拥有交易账户
- **WHEN** 用户在 `/trading` 提交买入指令
- **AND** 后端返回 409 `INSUFFICIENT_FUNDS`
- **THEN** 前端提示「可用资金不足，无法完成买入。请存入资金后重试。」

#### Scenario: Show mapped error when sell order is rejected by insufficient position
- **GIVEN** 用户已登录且拥有交易账户
- **WHEN** 用户在 `/trading` 提交卖出指令
- **AND** 后端返回 409 `INSUFFICIENT_POSITION`
- **THEN** 前端提示「可用持仓不足，无法完成卖出。请确认持仓数量。」

#### Scenario: Create a new trading account from accounts management page
- **GIVEN** 用户已登录
- **WHEN** 用户在 `/trading/accounts` 提交创建账户（accountName/initialCapital）
- **THEN** 前端调用 `POST /trading/accounts`
- **AND** 创建成功后新账户出现在账户列表中

#### Scenario: Handle risk assessment pending and allow evaluate on analytics page
- **GIVEN** 用户已登录且拥有交易账户
- **WHEN** 用户进入 `/trading/analytics` 并选择账户
- **AND** 后端返回 202 `RISK_ASSESSMENT_PENDING`
- **THEN** 前端展示「风险评估快照正在生成中」提示
- **WHEN** 用户点击「发起评估」
- **THEN** 前端调用 `POST /trading/accounts/{id}/risk-assessment/evaluate`
- **AND** 成功后展示风险评估快照（包含 assessmentId 等字段）
