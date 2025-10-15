## ADDED Requirements

### Requirement: 任务类型必须声明 SLA Policy

任务编排系统 MUST 为每个 `taskType` 声明稳定的 SLA Policy（至少包含：优先级、超时、最大重试次数、并发上限），并提供可查询输出用于门禁与运维治理。

#### Scenario: CLI 查询任务类型包含 SLA 字段

- **GIVEN** 运维需要核对系统任务治理策略
- **WHEN** 执行 `python -m job_orchestration.cli types`
- **THEN** 返回的每个任务类型包含 `priority/timeoutSeconds/maxRetries/concurrencyLimit`
- **AND** 字段命名使用 camelCase
