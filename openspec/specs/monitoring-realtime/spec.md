# monitoring-realtime Specification

## Purpose
统一实时监控 WebSocket 通道的鉴权语义：`/ws/monitor` 仅允许通过后端自管 `user-auth` 会话认证的用户连接，并为浏览器与 CLI 提供一致的 token 传递约定。
## Requirements
### Requirement: Monitor WebSocket Endpoint
后端 SHALL 在应用根路径暴露 `/ws/monitor` WebSocket 端点，并仅允许通过后端自管 `user-auth` 会话认证的用户建立连接。

会话令牌解析优先级 SHALL 为：`Authorization: Bearer <session_token>` > `Cookie: session_token=<session_token>`。

#### Scenario: 认证用户建立实时监控连接
- **GIVEN** 用户浏览器携带有效后端 session token（httpOnly Cookie）
- **WHEN** 前端连接 `ws(s)://<host>/ws/monitor`
- **THEN** 服务器以 101 状态接受握手
- **AND** 在 1 秒内发送至少一条结构合法的监控消息

#### Scenario: CLI 或服务端使用 Bearer token 连接
- **GIVEN** 客户端无法使用浏览器 Cookie（如 CLI）
- **WHEN** 握手请求通过 header 携带 `Authorization: Bearer <session_token>`
- **THEN** 服务器接受握手并建立连接

#### Scenario: 未认证访问被拒绝
- **GIVEN** 请求未携带可验证的会话令牌
- **WHEN** 客户端尝试连接 `/ws/monitor`
- **THEN** 服务器关闭连接，返回策略违规状态码（4401）

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

### Requirement: 实时监控端点必须由组合入口统一暴露
`/ws/monitor` MUST 通过统一后端组合入口对外暴露，保障与 REST 鉴权与治理策略一致。

#### Scenario: 通过组合入口建立监控连接
- **GIVEN** 统一组合入口已启动
- **WHEN** 客户端连接 `/ws/monitor`
- **THEN** 连接鉴权、日志脱敏、错误语义必须与其他上下文一致
- **AND** 不得绕过组合入口直接暴露独立监控服务

### Requirement: 监控系统必须提供摘要 REST 视图
实时监控能力 MUST 提供监控摘要 REST 接口，用于前端首屏与降级场景展示。

#### Scenario: 客户端读取监控摘要
- **GIVEN** 系统存在信号、告警、任务等运行数据
- **WHEN** 调用监控摘要接口
- **THEN** 返回结构化摘要数据
- **AND** 数据仅包含当前用户可访问范围

### Requirement: WS 频道与摘要语义必须一致
WebSocket 推送字段语义 MUST 与监控摘要保持一致，避免同一指标多种定义。

#### Scenario: WS 与 REST 的告警计数一致
- **GIVEN** 用户已订阅 `alerts` 频道
- **WHEN** 先读取摘要再接收 WS 推送
- **THEN** 两者中的告警计数字段语义一致
- **AND** 不泄露其他用户数据

