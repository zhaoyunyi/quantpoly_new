## Why

当前任务编排具备幂等与状态机骨架，但尚未与回测/信号/风控/交易领域任务形成统一桥接。
源项目中这些能力主要由 worker 任务承载。若不统一迁移，会造成“任务入口分散、状态口径不一致”。

## What Changes

- 扩展任务类型到回测、信号、风控、交易关键异步动作。
- 统一领域 API 的异步提交语义：返回 taskId + 可轮询状态。
- 统一重试/取消/冲突错误码与审计字段。

## Impact

- Affected specs:
  - `job-orchestration`
  - `backtest-runner`
  - `signal-execution`
  - `trading-account`
  - `risk-control`
- Affected code:
  - `libs/job_orchestration/*`
  - `libs/backtest_runner/*`
  - `libs/signal_execution/*`
  - `libs/trading_account/*`
  - `libs/risk_control/*`
