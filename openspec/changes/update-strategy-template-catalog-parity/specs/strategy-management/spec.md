## ADDED Requirements

### Requirement: 策略模板目录必须覆盖核心内置策略并提供参数 Schema
策略管理系统 MUST 提供内置策略模板目录，用于“零编程门槛”的策略创建与参数校验。

模板目录 MUST 至少覆盖以下模板（可按版本扩展）：

- `moving_average`
- `bollinger_bands`
- `rsi`
- `macd`
- `mean_reversion`
- `momentum`

每个模板 MUST 输出稳定字段：

- `templateId`
- `name`
- `requiredParameters`（类型、范围、描述、默认值）
- `defaults`（或等价字段，用于前端一键填充）

#### Scenario: 查询模板列表返回核心模板集合
- **GIVEN** 用户已认证
- **WHEN** 调用策略模板列表接口
- **THEN** 返回包含上述核心模板集合
- **AND** 每个模板均包含 `requiredParameters` 与默认值

#### Scenario: 从模板创建策略时进行参数校验
- **GIVEN** 用户选择一个模板并提交参数
- **WHEN** 参数缺失或超出范围
- **THEN** 后端拒绝创建并返回可识别的参数错误码
- **AND** 策略不会被创建
