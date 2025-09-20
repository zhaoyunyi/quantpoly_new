# risk-control Specification

## Purpose
TBD - created by archiving change add-risk-signal-context-migration. Update Purpose after archive.
## Requirements
### Requirement: 风控报警操作必须校验账户归属
确认、解决、批量确认、统计等报警操作 MUST 验证报警所属账户属于当前用户。

#### Scenario: 批量确认包含他人报警时拒绝
- **GIVEN** 批量确认请求中包含他人账户报警 ID
- **WHEN** 调用批量确认接口
- **THEN** 返回 403
- **AND** 不应更新任何越权报警记录

### Requirement: 风控统计接口必须按用户范围聚合
报警统计与未解决报警查询 MUST 仅返回当前用户可访问账户的数据。

#### Scenario: 指定 accountId 但不属于当前用户
- **GIVEN** 请求携带 `accountId` 且该账户不属于当前用户
- **WHEN** 调用统计或未解决报警接口
- **THEN** 返回 403
- **AND** 不泄露目标账户是否存在

### Requirement: 风险规则必须支持全生命周期治理
风控系统 MUST 提供风险规则的创建、更新、启停、删除与适用性查询能力。

#### Scenario: 用户查询账户适用规则
- **GIVEN** 用户账户存在多个规则来源
- **WHEN** 调用适用规则查询接口
- **THEN** 返回当前账户生效规则集合
- **AND** 不包含他人账户规则

### Requirement: 风险评估与告警处理必须可追踪
风控系统 MUST 支持账户/策略风险评估与告警处理闭环。

#### Scenario: 告警从 unresolved 到 resolved
- **GIVEN** 告警处于未解决状态
- **WHEN** 用户执行确认与解决操作
- **THEN** 告警状态迁移到已解决
- **AND** 记录操作人和时间戳

### Requirement: 风险评估必须支持账户快照查询与主动评估
风控系统 MUST 提供账户风险快照读取与主动 evaluate 触发能力。

#### Scenario: 主动触发账户风险评估
- **GIVEN** 用户账户存在持仓与交易数据
- **WHEN** 调用风险评估 evaluate 接口
- **THEN** 返回最新风险快照
- **AND** 快照包含风险分值、等级与建议

### Requirement: 风控巡检任务必须支持统一编排
风控任务编排 MUST 覆盖批量巡检、风险报告、告警通知、连续监控、风险快照生成等自动化任务。

#### Scenario: 提交风险报告任务并追踪状态
- **GIVEN** 用户请求生成日风险报告
- **WHEN** 系统提交任务
- **THEN** 返回可轮询 `taskId`
- **AND** 完成后返回结构化报告摘要

#### Scenario: 提交告警通知处理任务
- **GIVEN** 系统存在待通知告警
- **WHEN** 用户或系统触发通知处理任务
- **THEN** 返回任务状态句柄
- **AND** 任务结果包含成功/失败明细

### Requirement: 告警生命周期必须支持保留期清理策略
风控系统 MUST 支持按保留期清理历史告警，并保留审计信息。

#### Scenario: 清理超保留期告警
- **GIVEN** 系统存在已解决且超过保留期的告警
- **WHEN** 触发历史告警清理任务
- **THEN** 仅清理满足条件的告警
- **AND** 返回清理数量与任务审计标识

### Requirement: 风控系统必须提供规则统计与告警快捷查询
风控系统 MUST 提供规则统计、近期告警、未解决告警的快捷查询接口，以支撑监控与运营排障。

#### Scenario: 获取规则统计
- **GIVEN** 用户已配置多条风控规则
- **WHEN** 调用规则统计接口
- **THEN** 返回规则总数与按状态统计

#### Scenario: 获取近期告警与未解决告警
- **GIVEN** 用户存在多条告警记录
- **WHEN** 调用 `recent/unresolved` 快捷接口
- **THEN** 返回对应子集告警
- **AND** 仅返回当前用户可访问数据

### Requirement: 风控状态必须支持可持久化存储装配
风控上下文 MUST 支持在 sqlite 模式下使用持久化仓储，保证规则、告警、快照在服务重启后可恢复。

#### Scenario: 重启后仍可读取已存在告警
- **GIVEN** 用户已有已写入的风险告警与规则数据
- **WHEN** 服务重启后再次查询
- **THEN** 可读取重启前数据
- **AND** 查询范围仍受用户隔离约束

### Requirement: 风控仓储必须提供 sqlite 持久化适配器
风控上下文 MUST 提供 sqlite 持久化仓储实现，并在 sqlite 运行模式下作为默认写入路径。

#### Scenario: 告警与规则在重启后可恢复
- **GIVEN** 用户已有风控规则与告警记录
- **WHEN** 服务重启后再次查询
- **THEN** 返回重启前已提交数据
- **AND** 查询权限边界保持不变

