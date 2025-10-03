## ADDED Requirements

### Requirement: 市场资产目录必须支持单资产详情查询
市场数据服务 MUST 提供按 `symbol` 查询资产详情的能力。

#### Scenario: 查询单资产详情成功
- **GIVEN** 资产目录中存在目标 symbol
- **WHEN** 调用资产详情接口
- **THEN** 返回标准化资产详情字段
- **AND** 字段缺失时按约定返回缺省值

#### Scenario: 查询不存在 symbol
- **GIVEN** 目录中不存在目标 symbol
- **WHEN** 调用资产详情接口
- **THEN** 返回稳定的 not found 错误码
- **AND** 不返回 provider 内部错误细节

### Requirement: 资产目录查询必须支持过滤条件
市场数据目录查询 MUST 支持按市场与资产类别过滤。

#### Scenario: 按 market 过滤目录
- **GIVEN** 目录存在多市场资产
- **WHEN** 调用目录查询并传入 `market`
- **THEN** 返回满足条件的资产集合
- **AND** 响应保留总量信息用于前端分页/加载策略
