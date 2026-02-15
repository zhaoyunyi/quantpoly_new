## MODIFIED Requirements

### Requirement: 市场数据必须提供统一实时流网关

市场数据上下文 MUST 提供统一实时流订阅入口，用于输出实时行情事件。

实时流鉴权依赖 `get_current_user` MUST 显式接收 `request` 参数，并以关键字参数调用；系统 MUST NOT 通过 `try/except TypeError` 兼容无参或其他 legacy 签名。

#### Scenario: 建立订阅并接收行情事件
- **GIVEN** 用户已通过鉴权并请求订阅指定 symbol
- **WHEN** 实时流连接建立成功
- **THEN** 服务持续推送该 symbol 的行情事件
- **AND** 事件包含统一 envelope 字段（type/symbol/timestamp/payload）

#### Scenario: 鉴权回调签名不满足要求时拒绝初始化
- **GIVEN** 调用方提供 `get_current_user()`（不接收 `request`）
- **WHEN** 创建实时流 router
- **THEN** 系统 fail-fast 报错并拒绝初始化
- **AND** 不得在运行时回退尝试其他签名
