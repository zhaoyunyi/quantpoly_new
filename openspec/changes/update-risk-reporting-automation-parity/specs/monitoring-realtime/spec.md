## ADDED Requirements

### Requirement: 风控通知事件必须可订阅并可追踪
监控系统 MUST 支持风险通知任务事件推送，并与告警状态变更语义一致。

#### Scenario: 订阅 alerts 后接收通知处理结果
- **GIVEN** 客户端已订阅 `alerts` 频道
- **WHEN** 告警通知任务完成
- **THEN** 推送消息包含任务结果摘要
- **AND** 告警状态字段与 REST 查询保持一致
