# trading-account Specification

## Purpose
TBD - created by archiving change add-trading-account-context-migration. Update Purpose after archive.
## Requirements
### Requirement: 交易账户数据访问必须按用户隔离
交易账户、持仓、交易记录、资金流水相关接口 MUST 仅返回当前用户数据。

#### Scenario: 列表接口只返回当前用户账户
- **GIVEN** 系统中存在多个用户账户
- **WHEN** 当前用户调用账户列表接口
- **THEN** 返回结果仅包含 `userId == current_user.id` 的账户

### Requirement: 聚合统计必须基于用户权限范围
账户统计与分析 API MUST 只统计当前用户可访问的账户数据。

#### Scenario: 越权账户不参与统计
- **GIVEN** 请求参数包含他人账户 ID
- **WHEN** 调用统计接口
- **THEN** 返回 403 或忽略该账户并返回权限错误
- **AND** 不得混入他人数据

