## ADDED Requirements

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
