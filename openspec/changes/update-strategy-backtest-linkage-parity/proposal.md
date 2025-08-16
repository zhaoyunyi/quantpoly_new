## Why

当前策略管理与回测能力虽已分别存在，但“策略发起回测 -> 策略维度回测历史与统计”的研究闭环仍不完整。
这会导致策略研究链路出现孤岛任务，不利于产品愿景中的“策略优化与长期验证”。

## What Changes

- 补齐策略更新能力（含参数重校验）。
- 新增策略维度回测联动：从策略发起回测、查询策略回测列表、查询策略回测统计。
- 回测补齐删除闭环与策略关联一致性校验。

## Impact

- Affected specs:
  - `strategy-management`
  - `backtest-runner`
- Affected code:
  - `libs/strategy_management/*`
  - `libs/backtest_runner/*`
  - `apps/backend_app/router_registry.py`
