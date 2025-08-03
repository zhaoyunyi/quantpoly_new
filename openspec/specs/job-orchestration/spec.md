# job-orchestration Specification

## Purpose
TBD - created by archiving change add-job-orchestration-context-migration. Update Purpose after archive.
## Requirements
### Requirement: 后端长任务必须通过统一任务编排能力提交
回测、行情同步、交易批处理、风险巡检、信号批处理等长任务 MUST 通过统一任务编排层提交与追踪，不得由 API 直接执行阻塞流程。

#### Scenario: 提交任务返回可追踪 taskId
- **GIVEN** 用户发起回测或批处理请求
- **WHEN** 后端接受任务
- **THEN** 返回标准 envelope，包含 `taskId` 与初始状态
- **AND** 客户端可通过任务查询接口轮询状态

### Requirement: 任务必须具备幂等与所有权隔离
任务提交与查询 MUST 显式绑定 `userId`，并支持幂等键避免重复执行。

#### Scenario: 相同幂等键重复提交不会创建重复任务
- **GIVEN** 同一用户在有效窗口内重复提交同一业务任务且携带相同 `idempotencyKey`
- **WHEN** 后端处理请求
- **THEN** 返回同一 `taskId`
- **AND** 不得重复入队执行

#### Scenario: 越权查询任务被拒绝
- **GIVEN** 任务 `taskId` 不属于当前用户
- **WHEN** 调用任务查询接口
- **THEN** 返回 403
- **AND** 不泄露任务存在性细节

