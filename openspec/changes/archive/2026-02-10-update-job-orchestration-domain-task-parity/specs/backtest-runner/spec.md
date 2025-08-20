## ADDED Requirements

### Requirement: 回测提交必须支持任务编排桥接
回测系统 MUST 支持通过任务编排桥接提交异步执行任务。

#### Scenario: 回测创建后返回可追踪 taskId
- **GIVEN** 用户创建回测请求
- **WHEN** 系统采用任务编排模式处理
- **THEN** 返回回测任务与编排 taskId 关联信息
- **AND** 可查询其执行状态
