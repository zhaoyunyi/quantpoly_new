## ADDED Requirements

### Requirement: 回测结果必须支持统计与多任务对比
回测能力 MUST 提供统计聚合与多任务对比接口，支持策略研究决策。

#### Scenario: 用户对比多个回测任务
- **GIVEN** 用户提交多个已完成回测任务 ID
- **WHEN** 调用回测对比接口
- **THEN** 返回统一的对比指标结构
- **AND** 每个任务结果均经过用户所有权校验

### Requirement: 回测任务必须支持取消与可追踪状态
回测任务 MUST 支持取消与状态查询，并与任务编排状态机保持一致。

#### Scenario: 运行中任务被取消
- **GIVEN** 回测任务处于 `running`
- **WHEN** 用户发起取消请求
- **THEN** 任务状态迁移到 `cancelled`
- **AND** 后续查询能稳定返回取消状态与时间戳
