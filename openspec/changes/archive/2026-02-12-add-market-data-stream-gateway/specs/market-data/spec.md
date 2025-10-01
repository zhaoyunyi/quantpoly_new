## ADDED Requirements

### Requirement: 市场数据必须提供统一实时流网关
市场数据上下文 MUST 提供统一实时流订阅入口，用于输出实时行情事件。

#### Scenario: 建立订阅并接收行情事件
- **GIVEN** 用户已通过鉴权并请求订阅指定 symbol
- **WHEN** 实时流连接建立成功
- **THEN** 服务持续推送该 symbol 的行情事件
- **AND** 事件包含统一 envelope 字段（type/symbol/timestamp/payload）

#### Scenario: 非法订阅被拒绝
- **GIVEN** 用户请求订阅非法 channel 或超出限制
- **WHEN** 服务校验订阅请求
- **THEN** 返回稳定错误码
- **AND** 不创建无效订阅

### Requirement: 实时流必须具备退化与健康可观测能力
实时流服务 MUST 暴露连接健康状态，并在上游异常时提供退化语义。

#### Scenario: 上游流异常时进入退化模式
- **GIVEN** 上游行情流短时不可用
- **WHEN** 流网关检测到异常
- **THEN** 连接状态标记为 `degraded`
- **AND** 输出可恢复建议（例如轮询回退提示）
