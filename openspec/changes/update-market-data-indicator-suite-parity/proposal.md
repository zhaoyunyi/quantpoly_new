## Why

当前 `market-data` 的技术指标计算仅实现了最小 `SMA`，而源项目与产品愿景（策略模板、信号生成、回测报告）都依赖 `RSI/MACD/BOLL` 等常用指标。
如果指标套件不补齐：

- 策略模板只能停留在“配置展示”，无法形成可执行的研究闭环；
- `signal-execution` / `backtest-runner` 会被迫各自重复实现指标逻辑，破坏 DDD 边界与可维护性；
- 指标输出缺少统一的错误语义（unsupported/insufficient_data），前端无法稳定区分“参数错/数据不足/能力缺失”。

## What Changes

- 扩展 `MarketDataService.calculate_indicators` 指标集合：至少覆盖 `sma/ema/rsi/macd/bollinger`（按需求逐步扩展）。
- 统一每个指标的输出结构：`name`、`status`、`value`（可选）与必要的 `metadata`（如窗口期、参数）。
- 补齐 API/CLI 合同测试：覆盖成功、数据不足、未知指标三类语义。

## Impact

- Affected specs:
  - `market-data`
- Affected code:
  - `libs/market_data/*`
- Downstream dependencies:
  - `signal-execution`（策略驱动信号生成需要指标）
  - `backtest-runner`（回测引擎计算指标/信号）
