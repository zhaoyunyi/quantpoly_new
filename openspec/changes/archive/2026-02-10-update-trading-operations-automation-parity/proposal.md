## Why

当前交易域已覆盖账户生命周期与订单账本，但源项目中的交易运营自动化（待处理交易、日统计、风险巡检、批量执行、账户清理）尚未迁移。
缺失这部分能力会增加人工运维成本，并削弱交易系统长期运行稳定性。

## What Changes

- 补齐交易运营任务化能力并统一接入任务编排。
- 补齐日统计与风险巡检等运营读模型。
- 补齐账户清理任务的治理约束与审计语义。

## Impact

- Affected specs:
  - `trading-account`
- Affected code:
  - `libs/trading_account/*`
  - `libs/job_orchestration/*`
  - `libs/risk_control/*`
