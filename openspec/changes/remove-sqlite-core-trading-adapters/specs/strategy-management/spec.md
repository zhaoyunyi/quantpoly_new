## ADDED Requirements

### Requirement: 策略管理库不得再暴露 sqlite 持久化适配器
策略管理 capability MUST 不再把 sqlite 仓储作为受支持公开能力。

#### Scenario: 策略管理公开契约不包含 sqlite
- **GIVEN** 业务方通过策略管理库集成策略能力
- **WHEN** 检查公开导出与能力文档
- **THEN** 仅允许 `Postgres` 与 `InMemory` 作为可用仓储路径
- **AND** sqlite 仓储路径不再受支持
