## ADDED Requirements

### Requirement: 管理员动作必须集中治理
高风险动作（全局清理、批量维护、系统级开关） MUST 通过统一治理层授权，不得在业务路由中临时拼接权限逻辑。

#### Scenario: 普通用户调用管理员动作被拒绝
- **GIVEN** 普通用户已认证
- **WHEN** 调用系统级维护接口（例如全局清理）
- **THEN** 返回 403
- **AND** 不执行任何副作用

### Requirement: 高风险动作必须具备可审计性
治理层 MUST 记录管理员动作审计日志，至少包含 `actor/action/target/result/timestamp`。

#### Scenario: 管理员执行清理动作产生审计记录
- **GIVEN** 管理员执行高风险维护动作
- **WHEN** 动作执行完成（成功或失败）
- **THEN** 生成结构化审计记录
- **AND** 审计日志中的敏感字段（token/cookie/password）必须脱敏

