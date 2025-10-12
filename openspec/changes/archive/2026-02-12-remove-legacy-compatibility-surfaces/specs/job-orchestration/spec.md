## MODIFIED Requirements

### Requirement: 任务类型必须可注册并可查询

任务编排系统 MUST 提供任务类型注册表与查询能力，避免由业务代码散落硬编码 task type。

#### Scenario: CLI 查询任务类型注册表

- **GIVEN** 运维通过 CLI 查询任务类型
- **WHEN** 执行任务类型列表命令
- **THEN** 返回结构化任务类型清单
- **AND** 输出包含领域归属与可调度标记
- **AND** 输出 MUST NOT 包含 `legacyNames` 等迁移期兼容字段
