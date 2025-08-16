## Why

当前交易上下文以订单账本和分析接口为主，但账户生命周期（create/get/update/filter-config）与账户级风险评估闭环不完整。
这会增加前端拼装复杂度，且不利于“账户管理 + 风险评估”统一后端聚合。

## What Changes

- 补齐账户生命周期接口：创建、详情、更新、筛选配置。
- 补齐账户摘要与资金流水摘要读模型。
- 补齐账户风险评估快照查询与 evaluate 触发。

## Impact

- Affected specs:
  - `trading-account`
  - `risk-control`
- Affected code:
  - `libs/trading_account/*`
  - `libs/risk_control/*`
  - `apps/backend_app/router_registry.py`
