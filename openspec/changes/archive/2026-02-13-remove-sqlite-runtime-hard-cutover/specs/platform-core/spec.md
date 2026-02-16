## MODIFIED Requirements

### Requirement: 组合入口必须按配置装配持久化与行情 Provider
后端组合入口 MUST 根据运行时配置装配持久化适配器与市场数据 Provider，不得在生产场景隐式回退为 InMemory。

#### Scenario: postgres 模式装配持久化适配器
- **GIVEN** `storage_backend=postgres`
- **WHEN** 组合入口启动并装配上下文
- **THEN** 风控、信号、偏好等上下文使用可持久化适配器
- **AND** 不得隐式使用 InMemory 作为静默降级

#### Scenario: 缺失 postgres DSN 启动失败
- **GIVEN** `storage_backend=postgres`
- **AND** 未提供 `BACKEND_POSTGRES_DSN`
- **WHEN** 组合入口启动
- **THEN** 系统启动失败并返回可识别错误
- **AND** 错误信息不得泄露敏感配置值
