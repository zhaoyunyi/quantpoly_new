## ADDED Requirements

### Requirement: 市场数据运行时必须支持真实 Provider 装配
市场数据上下文 MUST 支持在运行时装配真实行情 provider（如 alpaca），并保持与 inmemory provider 一致的接口契约。

#### Scenario: 运行时切换到 alpaca provider
- **GIVEN** 配置 `market_data.provider=alpaca`
- **WHEN** 服务启动并提供行情查询
- **THEN** 查询链路使用 alpaca provider
- **AND** 返回结构与 inmemory provider 保持一致契约

#### Scenario: provider 配置非法时拒绝启动
- **GIVEN** 配置了不支持的 provider 名称
- **WHEN** 服务启动
- **THEN** 服务启动失败并返回可识别错误
- **AND** 不得静默回退到其他 provider
