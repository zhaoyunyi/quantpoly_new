# strategy-management Specification

## Purpose
TBD - created by archiving change add-strategy-backtest-migration. Update Purpose after archive.
## Requirements
### Requirement: 策略 CRUD 必须按用户隔离
后端 MUST 按 `current_user.id` 约束策略的创建、读取、更新与删除。

#### Scenario: 非所有者无法读取策略详情
- **GIVEN** 策略 `strategy_id` 不属于当前用户
- **WHEN** 调用 `GET /strategies/{strategy_id}`
- **THEN** 返回 403
- **AND** 响应不暴露该策略内部字段

### Requirement: 删除策略前必须检查回测占用
后端 MUST 在删除策略前检查是否存在 `pending/running` 回测任务。

#### Scenario: 存在运行中回测时阻止删除
- **GIVEN** 目标策略存在运行中回测任务
- **WHEN** 调用 `DELETE /strategies/{id}`
- **THEN** 返回 409
- **AND** 返回占用数量与可追踪错误码

