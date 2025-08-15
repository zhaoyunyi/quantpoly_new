## ADDED Requirements

### Requirement: 用户销毁动作必须纳入治理审计
管理员执行用户删除或注销代办动作 MUST 记录可追踪审计信息并受治理授权。

#### Scenario: 管理员删除用户时生成审计记录
- **GIVEN** 管理员具备用户治理权限
- **WHEN** 执行用户删除动作
- **THEN** 审计日志记录 `actor/action/target/result/timestamp`
- **AND** 敏感字段（token/cookie/password）必须脱敏
