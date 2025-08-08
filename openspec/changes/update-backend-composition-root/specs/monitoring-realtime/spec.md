## ADDED Requirements

### Requirement: 实时监控端点必须由组合入口统一暴露
`/ws/monitor` MUST 通过统一后端组合入口对外暴露，保障与 REST 鉴权与治理策略一致。

#### Scenario: 通过组合入口建立监控连接
- **GIVEN** 统一组合入口已启动
- **WHEN** 客户端连接 `/ws/monitor`
- **THEN** 连接鉴权、日志脱敏、错误语义必须与其他上下文一致
- **AND** 不得绕过组合入口直接暴露独立监控服务
