## MODIFIED Requirements

### Requirement: 市场数据必须支持技术指标计算任务
市场数据系统 MUST 提供技术指标计算任务接口，支持结构化输入输出与可复算，并至少覆盖策略研究所需的常用指标集合：

- `sma`（简单移动平均）
- `ema`（指数移动平均）
- `rsi`（相对强弱指标）
- `macd`（MACD 指标）
- `bollinger`（布林带）

每个指标输出 MUST 采用统一结构：

- `name`: 指标名（小写）
- `status`: `ok|unsupported|insufficient_data`
- `value`: 数值（仅当 `status=ok` 时必须存在）
- `metadata`: 参数回显（如 `period/stdDev/fast/slow/signal`）

#### Scenario: 计算 RSI 指标并返回数值
- **GIVEN** 系统存在标的的足量历史价格数据
- **WHEN** 用户提交 `rsi(period=14)` 指标计算任务
- **THEN** 返回 `status=ok` 且包含 `value`
- **AND** 输出包含 `metadata.period=14`

#### Scenario: 不支持的指标返回 unsupported
- **GIVEN** 用户提交未知指标名
- **WHEN** 系统执行指标计算
- **THEN** 对应指标输出 `status=unsupported`
- **AND** 响应 envelope 仍保持成功结构（由 `status` 表达不支持）

#### Scenario: 历史数据不足返回 insufficient_data
- **GIVEN** 系统历史数据长度不足以计算目标指标
- **WHEN** 用户提交指标计算任务
- **THEN** 对应指标输出 `status=insufficient_data`
- **AND** 不返回 `value` 字段
