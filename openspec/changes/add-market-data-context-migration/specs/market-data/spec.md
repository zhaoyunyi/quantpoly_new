## ADDED Requirements

### Requirement: 市场数据查询必须提供统一接口与错误语义
后端 MUST 提供统一的股票检索、行情与历史数据接口，并返回一致错误语义。

#### Scenario: 上游行情服务超时时返回可识别错误
- **GIVEN** 上游行情 Provider 超时
- **WHEN** 用户调用行情接口
- **THEN** 返回标准错误 envelope
- **AND** 错误码可用于前端区分重试与降级展示

### Requirement: 行情查询必须支持缓存与限流
高频行情接口 MUST 支持缓存与请求限流，以保障稳定性。

#### Scenario: 同一 symbol 短时间重复查询命中缓存
- **GIVEN** 用户短时间重复查询同一 symbol
- **WHEN** 请求命中缓存窗口
- **THEN** 后端直接返回缓存结果
- **AND** 响应中包含可观测的缓存命中标记（如 metadata）

