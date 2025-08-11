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

### Requirement: 策略状态变更必须持久化并在重启后可恢复
策略创建、更新、删除保护与状态变更 MUST 进入持久化路径，不得依赖 in-memory 主状态。

#### Scenario: 服务重启后策略状态可恢复
- **GIVEN** 用户已创建并更新策略状态
- **WHEN** 服务发生重启
- **THEN** 重新读取策略时必须返回重启前已提交状态
- **AND** 删除保护规则仍然生效

### Requirement: 策略必须支持模板化创建与受控状态迁移
策略管理 MUST 提供模板能力，并由领域状态机约束策略生命周期迁移。

#### Scenario: 从模板创建策略并成功激活
- **GIVEN** 用户选择一个可用策略模板
- **WHEN** 提交参数并创建策略后执行激活
- **THEN** 策略状态从 `draft` 迁移到 `active`
- **AND** 迁移过程记录参数校验结果

#### Scenario: 非法状态迁移被拒绝
- **GIVEN** 策略处于 `archived` 状态
- **WHEN** 用户尝试直接激活策略
- **THEN** 后端返回 409
- **AND** 错误码可用于前端识别状态冲突

