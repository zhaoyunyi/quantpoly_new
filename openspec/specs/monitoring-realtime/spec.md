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

### Requirement: 监控摘要与信号中心统计口径必须一致
监控摘要中的信号统计 MUST 与信号中心仪表板保持同一字段定义。

#### Scenario: 摘要与仪表板信号计数一致
- **GIVEN** 用户拥有已知数量的 pending/expired 信号
- **WHEN** 分别读取监控摘要与信号仪表板
- **THEN** 两者信号计数字段语义一致
- **AND** 数据范围均仅限当前用户

### Requirement: 风控通知事件必须可订阅并可追踪
监控系统 MUST 支持风险通知任务事件推送，并与告警状态变更语义一致。

#### Scenario: 订阅 alerts 后接收通知处理结果
- **GIVEN** 客户端已订阅 `alerts` 频道
- **WHEN** 告警通知任务完成
- **THEN** 推送消息包含任务结果摘要
- **AND** 告警状态字段与 REST 查询保持一致

### Requirement: 监控摘要必须覆盖运营核心指标
监控摘要 MUST 提供账户覆盖、活跃策略、运行中回测、运行中任务、信号与告警等核心运营指标。

#### Scenario: 读取监控摘要返回完整运营指标
- **GIVEN** 用户在多个上下文存在运行数据
- **WHEN** 调用 `/monitor/summary`
- **THEN** 返回账户、策略、回测、任务、信号、告警的结构化统计
- **AND** 所有指标均仅包含当前用户可访问范围

#### Scenario: 无运行数据时返回稳定空态结构
- **GIVEN** 用户当前无任何运行任务或信号
- **WHEN** 调用监控摘要接口
- **THEN** 返回字段完整且计数为 0
- **AND** 不省略约定字段

### Requirement: 监控摘要与任务编排状态必须语义一致
监控摘要中的任务统计 MUST 与任务编排系统状态语义一致，不得使用固定占位值。

#### Scenario: 任务运行中时摘要正确反映 running 数量
- **GIVEN** 用户存在处于 `running` 状态的任务
- **WHEN** 调用监控摘要接口
- **THEN** `tasks.running` 等于任务编排中当前用户的运行任务数
- **AND** 与任务查询接口统计一致

### Requirement: 监控摘要读模型必须可复算并提供 CLI

监控摘要属于跨上下文聚合查询。系统 MUST 提供可复用的监控摘要 Read Model 构建能力，并通过 CLI 以 JSON 输入/输出的方式支持复算与门禁校验。

#### Scenario: CLI 从 snapshot 复算运营摘要

- **GIVEN** 运维/测试提供一个包含 accounts/strategies/backtests/tasks/signals/alerts 的 JSON snapshot
- **WHEN** 执行 `python -m monitoring_realtime.cli summary --user-id <uid>` 并从 stdin 输入 snapshot JSON
- **THEN** stdout 输出 `success=true` 且包含运营摘要结构
- **AND** 摘要 `metadata.version` 为 `v2`
- **AND** 摘要计数字段与 snapshot 内容一致（仅统计当前 userId 范围）

