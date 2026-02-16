## ADDED Requirements

### Requirement: 风控库不得再暴露 sqlite 持久化适配器
风控 capability MUST 不再把 sqlite 仓储作为受支持公开能力。

#### Scenario: 风控公开契约不包含 sqlite
- **GIVEN** 业务方通过风控库集成规则与告警能力
- **WHEN** 检查公开导出与能力文档
- **THEN** 仅允许 `Postgres` 与 `InMemory` 作为可用仓储路径
- **AND** sqlite 路径不再受支持
