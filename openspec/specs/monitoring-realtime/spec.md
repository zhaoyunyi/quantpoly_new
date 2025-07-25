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
