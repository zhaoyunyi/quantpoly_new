## ADDED Requirements

### Requirement: 任务编排调度层不得再暴露 sqlite 调度适配器
任务编排 capability MUST 不再将 sqlite 调度器作为受支持运行时契约。

#### Scenario: 调度层公开契约不包含 sqlite 适配器
- **GIVEN** 业务方通过任务编排库集成调度能力
- **WHEN** 检查调度模块的公开能力与测试契约
- **THEN** 仅允许 `InMemory` 调度路径作为本地调度实现
- **AND** `SQLiteScheduler` 导入路径不再受支持
