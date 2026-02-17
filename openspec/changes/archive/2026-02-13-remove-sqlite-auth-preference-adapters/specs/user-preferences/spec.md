## ADDED Requirements

### Requirement: 偏好库不得再暴露 sqlite 持久化适配器
在 PostgreSQL 硬切完成后，`user-preferences` capability MUST 不再将 sqlite store 作为公开契约的一部分。

#### Scenario: 偏好库公开面仅保留 Postgres 与 InMemory
- **GIVEN** 业务方通过库公开 API 使用偏好能力
- **WHEN** 检查公开导出与文档约定
- **THEN** 必须仅包含 `Postgres` 与 `InMemory` 运行路径
- **AND** sqlite store 路径不再属于受支持能力
