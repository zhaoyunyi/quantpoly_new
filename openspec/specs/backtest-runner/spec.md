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

