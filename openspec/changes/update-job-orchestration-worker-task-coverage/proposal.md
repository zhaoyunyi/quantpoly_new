## Why

当前 `job-orchestration` 仅覆盖 6 个任务类型，无法承载源项目中的策略/信号/风控/交易/行情自动化任务族群。
若不先扩展编排底座，后续各域迁移会重复实现任务语义，导致状态机、幂等、审计口径不一致。

## What Changes

- 扩展任务类型覆盖到 Wave3 目标任务族（strategy/signal/risk/trading/market-data）。
- 引入任务类型注册与查询语义（含 CLI 输出），避免硬编码散落。
- 补齐调度侧的用户范围与命名空间规则，统一任务治理口径。

## Impact

- Affected specs:
  - `job-orchestration`
- Affected code:
  - `libs/job_orchestration/*`
  - `apps/backend_app/router_registry.py`
