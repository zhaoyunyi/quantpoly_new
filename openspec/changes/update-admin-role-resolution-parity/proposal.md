## Why

当前多处高风险接口用 `is_admin` 字段直接判权，而用户聚合以 `role/level` 建模。
这会导致管理员在部分接口被误判，形成“治理策略定义与运行时判定不一致”的安全缺陷。

## What Changes

- 建立统一管理员判定策略（优先 `role`，兼容 `is_admin` 作为迁移期兜底）。
- 交易运维与信号全局维护接口统一接入该策略。
- 管理员动作补充审计字段，确保判定来源可追踪。

## Impact

- Affected specs:
  - `trading-account`
  - `signal-execution`
  - `admin-governance`
- Affected code:
  - `libs/trading_account/*`
  - `libs/signal_execution/*`
  - `libs/admin_governance/*`
  - `libs/platform_core/*`
