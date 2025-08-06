## ADDED Requirements

### Requirement: 用户治理动作必须可审计
管理员对用户状态、等级、权限的治理动作 MUST 记录结构化审计日志。

#### Scenario: 管理员禁用用户生成审计记录
- **GIVEN** 管理员执行用户禁用操作
- **WHEN** 操作成功或失败
- **THEN** 审计日志记录 `actor/action/target/result/timestamp`
- **AND** 日志中不得包含明文密码或会话凭证
