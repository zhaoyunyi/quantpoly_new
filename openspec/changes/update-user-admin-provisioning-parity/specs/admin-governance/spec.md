## ADDED Requirements

### Requirement: 管理员开通用户动作必须可审计
治理系统 MUST 对管理员创建用户动作进行审计，记录关键上下文并脱敏敏感信息。

#### Scenario: 管理员开通用户写入审计日志
- **GIVEN** 管理员调用创建用户接口
- **WHEN** 操作成功或失败
- **THEN** 审计日志记录 `actor/action=admin_create_user/target/result/timestamp`
- **AND** 不包含明文密码或会话凭证
