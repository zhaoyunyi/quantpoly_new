## Why

当前 `backtest-runner` 仅提供回测任务状态机与对比统计接口，但并未真正执行“回测引擎”计算（`/backtests/tasks` 目前只是创建 job 并立即 succeed）。
这会导致产品核心链路缺失：

- “一键回测”无法产出可解释的权益曲线与指标；
- 策略模板与信号系统无法通过回测验证正确性；
- 回测结果无法作为后续“策略对比/优化建议”的数据基础。

源项目已提供最小回测引擎（均线交叉等），因此需要在当前仓库以 DDD + Library-First 的方式补齐。

## What Changes

- 在 `backtest-runner` 内引入最小回测引擎：基于市场历史数据与策略模板/参数计算权益曲线与指标。
- 为回测结果增加独立存储（迁移期可先 in-memory，后续可落 SQLite/Postgres），支持结果读取。
- 更新 `/backtests/tasks`：真实执行引擎并回填 `BacktestTask.metrics`，失败时写入 job error。
- 补齐 API/CLI 合同测试，确保“先红后绿”。

## Impact

- Affected specs:
  - `backtest-runner`
- Affected code:
  - `libs/backtest_runner/*`
- Dependencies:
  - `market-data`（历史行情）
  - `strategy-management`（模板参数与策略状态）
  - `job-orchestration`（任务状态与幂等）
