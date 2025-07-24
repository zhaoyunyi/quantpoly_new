# backend-user-ownership Specification

## Purpose
统一后端“资源所有权（ownership）”规则：所有受保护资源必须绑定 `userId`，并且在任何读写操作中基于 `current_user.id` 强制过滤与校验，防止越权访问。
## Requirements
### Requirement: 所有业务资源必须绑定 userId
所有业务资源（策略、回测、交易账户、信号、风控规则、告警等） MUST 绑定 `userId`，并在读写时强制执行所有权校验。

#### Scenario: 列表接口按当前用户过滤
- **GIVEN** 当前用户为 `current_user`
- **WHEN** 调用任意资源列表接口
- **THEN** 返回的数据 MUST 仅包含 `userId == current_user.id` 的资源

#### Scenario: 读取单个资源拒绝越权
- **GIVEN** 当前用户为 `current_user`
- **AND** 某资源的 `userId != current_user.id`
- **WHEN** 用户尝试读取该资源
- **THEN** 后端 MUST 返回 403

#### Scenario: 更新/删除资源拒绝越权
- **GIVEN** 当前用户为 `current_user`
- **AND** 某资源的 `userId != current_user.id`
- **WHEN** 用户尝试更新或删除该资源
- **THEN** 后端 MUST 返回 403

### Requirement: Repository/Service 层必须显式接收 user_id
对外暴露的 Repository/Service 方法 MUST 显式接收 `user_id` 参数，避免隐式全局查询导致越权。

#### Scenario: get_by_id 必须校验 user_id
- **GIVEN** repository 方法 `get_by_id(id, user_id)`
- **WHEN** id 存在但 `userId != user_id`
- **THEN** 返回 None 或抛出 domain error（由路由映射为 403）
