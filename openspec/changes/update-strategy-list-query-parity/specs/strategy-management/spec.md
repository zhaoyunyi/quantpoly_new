## ADDED Requirements

### Requirement: 策略列表必须支持分页与条件查询
策略管理接口 MUST 支持按状态和关键词查询，并返回稳定分页结构。

#### Scenario: 按状态筛选并分页查询策略
- **GIVEN** 用户拥有多个不同状态策略
- **WHEN** 调用 `GET /strategies` 并传入 `status`、`page`、`pageSize`
- **THEN** 返回该用户范围内满足条件的分页结果
- **AND** 响应包含 `items`、`total`、`page`、`pageSize`

#### Scenario: 按关键词搜索策略名称
- **GIVEN** 用户拥有多条策略记录
- **WHEN** 调用 `GET /strategies` 并传入 `search`
- **THEN** 仅返回名称匹配关键词的策略
- **AND** 不得泄漏其他用户策略
