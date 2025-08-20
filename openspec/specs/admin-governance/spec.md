# admin-governance Specification

## Purpose
TBD - created by archiving change add-admin-governance-context-migration. Update Purpose after archive.
## Requirements
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

### Requirement: 用户治理动作必须可审计
管理员对用户状态、等级、权限的治理动作 MUST 记录结构化审计日志。

#### Scenario: 管理员禁用用户生成审计记录
- **GIVEN** 管理员执行用户禁用操作
- **WHEN** 操作成功或失败
- **THEN** 审计日志记录 `actor/action/target/result/timestamp`
- **AND** 日志中不得包含明文密码或会话凭证

### Requirement: 用户销毁动作必须纳入治理审计
管理员执行用户删除或注销代办动作 MUST 记录可追踪审计信息并受治理授权。

#### Scenario: 管理员删除用户时生成审计记录
- **GIVEN** 管理员具备用户治理权限
- **WHEN** 执行用户删除动作
- **THEN** 审计日志记录 `actor/action/target/result/timestamp`
- **AND** 敏感字段（token/cookie/password）必须脱敏

### Requirement: 治理层必须统一解释管理员身份来源
治理系统 MUST 统一解释管理员身份来源（`role/level/is_admin`），并记录最终判定依据。

#### Scenario: 管理员身份来源可追踪
- **GIVEN** 系统接收到高风险管理员动作
- **WHEN** 治理层完成鉴权与执行
- **THEN** 审计记录包含 `role/level/is_admin` 的判定摘要
- **AND** 敏感字段保持脱敏

