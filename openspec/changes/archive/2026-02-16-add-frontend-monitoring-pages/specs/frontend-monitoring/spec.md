## ADDED Requirements

### Requirement: Frontend SHALL provide a real-time monitor page backed by WS /ws/monitor

前端 SHALL 在 `/monitor` 提供实时监控页面，并通过后端 `WS /ws/monitor` 获取 signals/alerts 更新。

#### Scenario: Subscribe to signals and alerts channels
- **GIVEN** 用户已登录且浏览器携带 `session_token` cookie
- **WHEN** 前端连接 `WS /ws/monitor` 并发送 `subscribe`
- **THEN** 后端返回 `subscribed`
- **AND** 后端推送 `signals_update` 与 `risk_alert` 消息

