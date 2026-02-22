# frontend-backtest-center Specification

## Purpose
TBD - created by archiving change add-frontend-backtest-center-pages. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL provide backtest list and submission flow

前端 SHALL 在 `/backtests` 提供回测任务列表与创建能力。

#### Scenario: Create backtest task
- **GIVEN** 用户已登录且拥有某策略
- **WHEN** 用户提交回测创建表单
- **THEN** 前端调用 `POST /backtests`（或 `POST /backtests/tasks`）
- **AND** 在列表中展示新任务状态

### Requirement: Frontend SHALL provide backtest detail and result view

前端 SHALL 在 `/backtests/$id` 提供回测详情与结果展示，并处理“结果未就绪”的中间态。

#### Scenario: Backtest result not ready
- **GIVEN** 回测仍在运行或刚结束
- **WHEN** 前端调用 `GET /backtests/{id}/result` 返回 `BACKTEST_RESULT_NOT_READY`
- **THEN** 前端展示“结果生成中”提示
- **AND** 提供刷新/重试入口

