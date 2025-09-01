## 设计目标

- 让信号生成从“手工录入”升级为“策略驱动评估”。
- 遵循 `spec/DDDSpec.md`：跨上下文通过 ACL/OHS，不直接依赖对方仓储/模型。
- 保持 `signal-execution` 的通用语言：`TradingSignal` 仍是信号域聚合根；策略与行情只作为输入。

## 依赖注入与 ACL 形状

在 `SignalExecutionService` 中新增可选依赖（回调或 Protocol）：

- `strategy_reader(user_id, strategy_id) -> {templateId, parameters, status}`
  - 只暴露信号生成所需字段，不泄露策略域内部模型。
- `market_history_reader(user_id, symbol, start_date, end_date, timeframe) -> list[candle]`
  - candle 至少包含 `timestamp/open/high/low/close/volume`。
- （可选）`indicator_calculator(...)`
  - 默认走 `market-data` 的 indicators 能力，避免重复实现。

> 说明：如果未来要支持批量策略/批量账户生成，可在此 ACL 上层再引入 batch API，但本变更先保证单策略单账户的闭环。

## API 形态建议

建议新增端点而非隐式复用已有 `/signals/generate`：

- `POST /signals/generate-by-strategy`
  - 输入：`strategyId`、`accountId`、可选 `symbols`（覆盖策略默认 universe）、可选 `asOf`。
  - 输出：`signals[]` + `skipped[]`（原因：insufficient_data / no_signal）。

这样可避免把“手工生成”和“策略驱动生成”混在同一语义里。

## 可测试性

- 使用 in-memory market provider + 固定 candle 序列，保证指标与信号结果可预测。
- Given/When/Then 场景覆盖：inactive 策略、数据不足、策略触发信号。
