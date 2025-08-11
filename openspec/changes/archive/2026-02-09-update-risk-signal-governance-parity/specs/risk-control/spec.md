## ADDED Requirements

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
