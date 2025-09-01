## ADDED Requirements

### Requirement: 回测任务必须真实执行引擎并产出可读取结果
回测系统 MUST 在提交回测任务后真实执行回测引擎计算，并产出可读取的结构化结果（指标 + 权益曲线/交易明细）。

该能力 MUST 满足：

- 结果可复算：同一输入在相同市场数据下输出可重复。
- 用户隔离：仅允许任务所有者读取结果。
- 与任务编排一致：通过 `job-orchestration` 返回可追踪 `taskId` 与状态。

#### Scenario: 提交回测任务后返回指标并可读取结果
- **GIVEN** 用户拥有可执行策略与可访问行情数据
- **WHEN** 提交回测任务（task mode）
- **THEN** 返回 `taskId` 与 `completed/succeeded` 状态
- **AND** 回测任务包含结构化 `metrics`
- **AND** 可通过结果读取接口返回权益曲线与交易明细

#### Scenario: 越权读取回测结果被拒绝
- **GIVEN** 回测任务不属于当前用户
- **WHEN** 调用结果读取接口
- **THEN** 返回 403
- **AND** 不泄露任务是否存在
