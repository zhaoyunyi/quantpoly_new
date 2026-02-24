## ADDED Requirements

### Requirement: 平台核心必须提供存储契约防回流门禁
平台核心 MUST 提供可自动执行的存储契约门禁，用于校验核心库公开导出中不得回流 sqlite 适配器能力。

#### Scenario: 默认门禁通过核心库导出校验
- **GIVEN** 系统执行默认 `storage-contract-gate`
- **WHEN** 校验核心上下文库公开导出
- **THEN** 返回结构化 JSON 结果
- **AND** 当不存在 sqlite 导出时 `allowed=true`

#### Scenario: 发现 sqlite 导出时门禁阻断
- **GIVEN** 门禁输入包含存在 sqlite 导出的模块
- **WHEN** 执行 `storage-contract-gate`
- **THEN** 返回 `allowed=false`
- **AND** 返回模块级违规明细用于回归定位
