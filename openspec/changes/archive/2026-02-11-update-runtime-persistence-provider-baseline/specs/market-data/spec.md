## ADDED Requirements

### Requirement: 行情 Provider 必须支持运行时可配置装配
市场数据上下文 MUST 支持通过运行时配置选择 provider（至少支持 `inmemory` 与 `alpaca`），并向上层暴露一致错误语义。

#### Scenario: 选择 alpaca provider 并成功装配
- **GIVEN** 运行时配置 `market_data.provider=alpaca`
- **WHEN** 组合入口启动并创建市场数据服务
- **THEN** 市场数据服务使用 alpaca provider
- **AND** `provider-health` 能返回对应 provider 标识

#### Scenario: provider 装配失败返回统一错误
- **GIVEN** provider 初始化失败（如配置缺失）
- **WHEN** 服务处理市场数据请求
- **THEN** 返回统一错误 envelope
- **AND** 错误码可用于区分配置错误与上游错误
