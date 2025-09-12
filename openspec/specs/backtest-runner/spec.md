# backtest-runner Specification

## Purpose
TBD - created by archiving change add-strategy-backtest-migration. Update Purpose after archive.
## Requirements
### Requirement: 回测任务状态机必须可观测
回测任务 MUST 遵循 `pending -> running -> completed|failed|cancelled` 的状态机，并支持查询。

#### Scenario: 创建回测任务后可轮询状态
- **GIVEN** 用户创建回测任务
- **WHEN** 轮询任务状态接口
- **THEN** 能按顺序观察状态迁移
- **AND** 完成后可读取结构化结果指标

### Requirement: 回测任务必须绑定用户与策略
回测任务 MUST 绑定 `userId` 与 `strategyId`，并在读取时执行所有权校验。

#### Scenario: 越权读取回测任务被拒绝
- **GIVEN** 回测任务不属于当前用户
- **WHEN** 调用回测详情接口
- **THEN** 返回 403
- **AND** 不返回任务执行细节

### Requirement: 回测任务状态必须持久化并支持幂等提交
回测任务的创建与状态迁移 MUST 持久化存储，并支持幂等键避免重复任务。

#### Scenario: 相同幂等键不会重复创建回测任务
- **GIVEN** 同一用户重复提交相同回测请求且幂等键一致
- **WHEN** 系统处理任务创建
- **THEN** 必须返回同一任务标识
- **AND** 不得产生重复任务记录

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

### Requirement: 回测任务必须支持策略联动触发与删除闭环
回测系统 MUST 支持从策略域触发任务，并提供删除闭环能力。

#### Scenario: 删除已完成回测任务
- **GIVEN** 回测任务处于 `completed/failed/cancelled`
- **WHEN** 用户发起删除请求
- **THEN** 任务被成功删除
- **AND** 删除行为可追踪

### Requirement: 回测提交必须支持任务编排桥接
回测系统 MUST 支持通过任务编排桥接提交异步执行任务。

#### Scenario: 回测创建后返回可追踪 taskId
- **GIVEN** 用户创建回测请求
- **WHEN** 系统采用任务编排模式处理
- **THEN** 返回回测任务与编排 taskId 关联信息
- **AND** 可查询其执行状态

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

### Requirement: 回测任务必须支持用户级重命名管理
回测系统 MUST 支持用户对本人回测任务进行重命名，以便在策略研究过程中标注实验意图。

#### Scenario: 用户重命名自己的回测任务
- **GIVEN** 当前用户拥有一个已创建的回测任务
- **WHEN** 调用回测重命名接口并提交 `displayName`
- **THEN** 回测任务名称被更新
- **AND** 更新时间戳发生变化

#### Scenario: 越权重命名被拒绝
- **GIVEN** 回测任务不属于当前用户
- **WHEN** 用户调用重命名接口
- **THEN** 返回 403
- **AND** 不泄露任务详细信息

### Requirement: 回测任务必须支持同策略相关结果聚合查询
回测系统 MUST 提供“相关回测”查询能力，用于按同一策略聚合同用户历史任务并支持过滤。

#### Scenario: 查询同策略相关回测
- **GIVEN** 用户在同一策略下存在多个回测任务
- **WHEN** 调用相关回测查询接口并传入 `limit/status`
- **THEN** 返回同策略的回测列表
- **AND** 结果排除当前任务

#### Scenario: 相关回测查询仅返回当前用户数据
- **GIVEN** 不同用户在同一策略 ID 下均有回测任务
- **WHEN** 当前用户调用相关回测查询
- **THEN** 仅返回当前用户任务
- **AND** 不返回其他用户任务

