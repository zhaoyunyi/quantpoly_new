## ADDED Requirements

### Requirement: Frontend SHALL provide a dashboard overview page

前端 SHALL 在 `/dashboard` 提供总览页面，并展示账户/策略/回测/任务/信号/告警的关键结论。

#### Scenario: Dashboard loads operational summary
- **GIVEN** 用户已登录
- **WHEN** 打开 `/dashboard`
- **THEN** 前端调用 `GET /monitor/summary`
- **AND** 展示 accounts/strategies/backtests/tasks/signals/alerts 的统计卡片

#### Scenario: Dashboard shows degraded banner when sources are unavailable
- **GIVEN** `GET /monitor/summary` 返回 `degraded.enabled=true`
- **WHEN** 渲染 Dashboard
- **THEN** 页面展示降级提示与原因列表

