## ADDED Requirements

### Requirement: 监控消息必须使用标准 envelope
实时监控通道 MUST 统一消息结构为 `type`、`payload`、`data`、`timestamp`。

#### Scenario: 服务端响应 ping 返回标准 pong
- **GIVEN** 客户端发送 `{"type":"ping","timestamp":1700000000}`
- **WHEN** 服务端处理该消息
- **THEN** 返回 `type="pong"`
- **AND** `payload.echo` 与原时间戳一致
- **AND** 返回消息包含 `timestamp`

### Requirement: 监控频道订阅必须可控
服务端 MUST 支持 `subscribe/unsubscribe` 对 signals/alerts 频道进行控制。

#### Scenario: 未订阅频道不推送对应消息
- **GIVEN** 客户端取消订阅 `alerts`
- **WHEN** 系统产生新的风险告警
- **THEN** 该连接不应接收 `risk_alert` 消息
- **AND** 连接保持正常

### Requirement: 推送数据必须经过用户权限过滤
`signals_update` 与 `risk_alert` 推送 MUST 仅包含当前用户可访问账户的数据。

#### Scenario: 存在他人账户信号时不推送
- **GIVEN** 信号池中同时存在当前用户与他人账户信号
- **WHEN** 服务端推送 `signals_update`
- **THEN** 消息内仅包含当前用户账户信号
- **AND** 不泄露他人账户标识

