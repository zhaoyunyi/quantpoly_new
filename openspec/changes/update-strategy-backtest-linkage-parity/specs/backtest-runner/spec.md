## ADDED Requirements

### Requirement: 回测任务必须支持策略联动触发与删除闭环
回测系统 MUST 支持从策略域触发任务，并提供删除闭环能力。

#### Scenario: 删除已完成回测任务
- **GIVEN** 回测任务处于 `completed/failed/cancelled`
- **WHEN** 用户发起删除请求
- **THEN** 任务被成功删除
- **AND** 删除行为可追踪
