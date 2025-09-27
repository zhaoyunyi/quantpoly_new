## ADDED Requirements

### Requirement: Alpaca Provider 必须具备可运行 transport 实现
当配置 `provider=alpaca` 时，市场数据服务 MUST 使用可运行的 transport 调用链路，不得使用占位抛错实现。

#### Scenario: 配置合法时 alpaca 查询可用
- **GIVEN** 系统已配置合法 alpaca 访问参数
- **WHEN** 用户调用 quote 或 history 接口
- **THEN** 请求通过 alpaca transport 执行
- **AND** 返回统一市场数据响应结构

#### Scenario: 配置缺失时启动或请求 fail-fast
- **GIVEN** provider 设置为 alpaca 但关键配置缺失
- **WHEN** 服务启动或处理请求
- **THEN** 返回稳定可识别错误
- **AND** 不得静默回退为 inmemory 数据

### Requirement: Market Data CLI 必须支持真实 provider 装配
`market_data` CLI MUST 支持通过参数/环境变量装配真实 provider，并保持与 API 相同错误语义。

#### Scenario: CLI 在 alpaca 超时场景返回统一错误码
- **GIVEN** CLI 使用 alpaca provider
- **WHEN** 上游请求超时
- **THEN** CLI 输出标准错误 envelope
- **AND** 错误码与 API 行为一致
