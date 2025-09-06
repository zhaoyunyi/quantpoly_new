## ADDED Requirements

### Requirement: 信号生成必须支持策略驱动的市场数据评估
信号系统 MUST 支持“策略驱动信号生成”：根据 `strategyId` 的模板与参数，对指定账户与标的进行市场数据评估后生成 `BUY/SELL` 信号。

该能力 MUST 满足：

- 保持用户隔离：仅能生成当前用户可访问策略与账户的信号。
- 数据不足时可解释：当历史数据不足以计算指标时，系统 MUST 返回可识别的跳过原因。
- 跨上下文依赖必须通过 ACL/OHS：禁止直接引用策略域/行情域的仓储或内部模型。

#### Scenario: 策略处于 inactive 时不生成信号
- **GIVEN** 策略不处于可执行状态（如 `draft/archived`）
- **WHEN** 用户请求策略驱动生成
- **THEN** 返回空信号集合
- **AND** 返回可识别原因（如 `strategy_inactive`）

#### Scenario: 历史数据不足时返回跳过原因
- **GIVEN** 标的历史数据不足以计算指标
- **WHEN** 用户请求策略驱动生成
- **THEN** 系统不生成该标的信号
- **AND** 在响应中返回 `insufficient_data` 跳过原因

#### Scenario: 策略触发条件满足时生成 BUY/SELL 信号
- **GIVEN** 标的历史数据满足指标计算窗口
- **AND** 策略触发条件满足（如均线金叉/RSI 超卖）
- **WHEN** 用户请求策略驱动生成
- **THEN** 系统生成对应 `BUY/SELL` 信号
- **AND** 信号后续可被处理与执行接口消费
