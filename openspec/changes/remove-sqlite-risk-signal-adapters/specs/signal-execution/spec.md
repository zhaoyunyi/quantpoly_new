## ADDED Requirements

### Requirement: 信号库不得再暴露 sqlite 持久化适配器
信号执行 capability MUST 不再把 sqlite 仓储作为受支持公开能力。

#### Scenario: 信号公开契约不包含 sqlite
- **GIVEN** 业务方通过信号库集成信号与执行能力
- **WHEN** 检查公开导出与能力文档
- **THEN** 仅允许 `Postgres` 与 `InMemory` 作为可用仓储路径
- **AND** sqlite 路径不再受支持
