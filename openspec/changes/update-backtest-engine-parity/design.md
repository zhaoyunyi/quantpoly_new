## 设计目标

- 让回测从“任务占位”升级为“可复算引擎执行”。
- 保持 bounded context：回测域不直连策略域/行情域仓储，仅通过 ACL 获取输入。
- 迁移期优先实现最小可用引擎（先覆盖 `moving_average/mean_reversion`），确保指标口径稳定。

## 引擎输入/输出

### 输入（BacktestConfig）

- `strategyId`
- `templateId` + `parameters`（由 `strategy_reader` 提供）
- `symbol` 或 `symbols`（先支持单标的）
- `startDate/endDate/timeframe`
- `initialCapital`、`commissionRate`（可选）

### 输出（BacktestResult）

- `equityCurve[]`：`{timestamp, equity}`
- `dailyReturns[]`
- `trades[]`
- `metrics`：`returnRate/maxDrawdown/sharpeRatio/tradeCount/winRate`（最小集合）

## 结果存储

- 引入 `BacktestResultStore`：
  - in-memory：用于测试与迁移期
  - sqlite：用于组合入口的持久化模式

结果读取 API 建议：

- `GET /backtests/{taskId}/result`

## 任务编排联动

- `/backtests/tasks` 提交 `job_orchestration` 的 `backtest_run` task。
- 在迁移期保持“同步执行 + job 封装”的范式（与 market-data/risk-control 一致），但必须真实执行引擎并写入结果。
