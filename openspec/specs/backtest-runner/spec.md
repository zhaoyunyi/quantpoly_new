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

