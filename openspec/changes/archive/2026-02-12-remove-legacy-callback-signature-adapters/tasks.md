## 1. Spec Delta（治理约束）

- [x] 1.1 更新 `backend-user-ownership`：明确跨上下文回调/适配器必须显式接收 `user_id`，禁止 legacy 签名回退。
- [x] 1.2 运行 `openspec validate remove-legacy-callback-signature-adapters --strict`

## 2. Strategy / Backtest Linkage（回调签名收敛）

- [x] 2.1（Red）新增测试：`StrategyService` 传入旧签名 `count_active_backtests(strategy_id)` 时必须拒绝（不允许静默回退）
- [x] 2.2（Green）移除 `StrategyService._call_maybe_legacy_count/_call_required` 回退路径；改为强制关键字参数调用并做签名校验
- [x] 2.3 更新 `strategy_management` 相关测试与 CLI 默认 service 构造，统一使用 `count_active_backtests(*, user_id, strategy_id)`

## 3. Backtest Runner 回调收敛

- [x] 3.1（Red）新增测试：`BacktestService` 传入旧签名 `strategy_reader(strategy_id)` / `market_history_reader(symbol)` 时必须拒绝
- [x] 3.2（Green）移除 `BacktestService` 的 `TypeError` 回退调用；改为关键字参数调用并做签名校验

## 4. Signal Execution 回调收敛

- [x] 4.1（Red）新增测试：`SignalExecutionService` 传入旧签名 `strategy_reader(strategy_id)` / `market_history_reader(symbol)` 时必须拒绝
- [x] 4.2（Green）移除 `SignalExecutionService` 的 `TypeError` 回退调用；改为关键字参数调用并做签名校验

## 5. Trading Account 风险回调收敛

- [x] 5.1（Red）新增测试：风险 reader/evaluator 不接受关键字参数时必须拒绝
- [x] 5.2（Green）移除 `TradingAccountService` 的 `TypeError` 回退调用；改为关键字参数调用并做签名校验

## 6. 回归与归档

- [x] 6.1 运行 `ruff check .`
- [x] 6.2 运行 `pytest -q`
- [x] 6.3 使用 `git cnd` 提交
- [x] 6.4 执行 `openspec archive remove-legacy-callback-signature-adapters --yes`
