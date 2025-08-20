## ADDED Requirements

### Requirement: 交易运维接口必须采用统一管理员判定策略
交易运维接口（待处理订单、价格刷新）MUST 使用统一管理员判定策略，不得直接依赖单一字段。

#### Scenario: 角色为 admin 的用户可执行价格刷新
- **GIVEN** 当前用户 `role=admin`
- **WHEN** 调用价格刷新接口
- **THEN** 请求通过并执行刷新逻辑
- **AND** 审计记录包含判权来源
