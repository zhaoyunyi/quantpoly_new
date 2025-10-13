## ADDED Requirements

### Requirement: 监控摘要读模型必须可复算并提供 CLI

监控摘要属于跨上下文聚合查询。系统 MUST 提供可复用的监控摘要 Read Model 构建能力，并通过 CLI 以 JSON 输入/输出的方式支持复算与门禁校验。

#### Scenario: CLI 从 snapshot 复算运营摘要

- **GIVEN** 运维/测试提供一个包含 accounts/strategies/backtests/tasks/signals/alerts 的 JSON snapshot
- **WHEN** 执行 `python -m monitoring_realtime.cli summary --user-id <uid>` 并从 stdin 输入 snapshot JSON
- **THEN** stdout 输出 `success=true` 且包含运营摘要结构
- **AND** 摘要 `metadata.version` 为 `v2`
- **AND** 摘要计数字段与 snapshot 内容一致（仅统计当前 userId 范围）
