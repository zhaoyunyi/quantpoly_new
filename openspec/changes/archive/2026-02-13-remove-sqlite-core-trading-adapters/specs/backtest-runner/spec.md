## ADDED Requirements

### Requirement: 回测库不得再暴露 sqlite 持久化适配器
回测 capability MUST 不再把 sqlite 仓储与 sqlite 结果存储作为受支持公开能力。

#### Scenario: 回测公开契约不包含 sqlite
- **GIVEN** 业务方通过回测库集成任务与结果能力
- **WHEN** 检查公开导出与能力文档
- **THEN** 仅允许 `Postgres` 与 `InMemory` 作为可用持久化路径
- **AND** sqlite 路径不再受支持
