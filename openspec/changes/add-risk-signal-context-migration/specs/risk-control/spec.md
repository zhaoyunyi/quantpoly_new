## ADDED Requirements

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

