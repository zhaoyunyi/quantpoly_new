## ADDED Requirements

### Requirement: 用户认证库不得再暴露 sqlite 持久化适配器
在 PostgreSQL 硬切完成后，`user-auth` capability MUST 不再将 sqlite 适配器作为公开契约的一部分。

#### Scenario: 认证库公开面仅保留 Postgres 与 InMemory
- **GIVEN** 业务方通过库公开 API 使用认证能力
- **WHEN** 检查公开导出与文档约定
- **THEN** 必须仅包含 `Postgres` 与 `InMemory` 运行路径
- **AND** sqlite 适配器路径不再属于受支持能力
