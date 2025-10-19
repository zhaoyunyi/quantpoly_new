## MODIFIED Requirements

### Requirement: Repository/Service 层必须显式接收 user_id

对外暴露的 Repository/Service 方法 MUST 显式接收 `user_id` 参数，避免隐式全局查询导致越权。

跨上下文交互（ACL/OHS、回调、适配器）同样 MUST 显式接收 `user_id` 与资源标识（如 `strategy_id/account_id/symbol`），并以关键字参数调用。

系统 MUST NOT 通过 `try/except TypeError` 等方式兼容“省略 user_id 的 legacy 签名”。

#### Scenario: get_by_id 必须校验 user_id

- **GIVEN** repository 方法 `get_by_id(id, user_id)`
- **WHEN** id 存在但 `userId != user_id`
- **THEN** 返回 None 或抛出 domain error（由路由映射为 403）

#### Scenario: 跨上下文回调必须显式接收 user_id

- **GIVEN** service 依赖跨上下文回调 `callback(*, user_id, strategy_id, ...)`
- **WHEN** 以关键字参数调用该回调
- **THEN** 回调可以在 user scope 内执行查询/校验
- **AND** 系统不得尝试以旧签名（仅 `strategy_id` 等）回退调用
