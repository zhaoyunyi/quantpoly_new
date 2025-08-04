## Why

源项目交易域拆分为 `trading_accounts.py + trading.py`，覆盖账户、订单、成交、资金流水、统计分析等完整链路；当前仓库 `trading-account` 仅提供账户与持仓基础查询，无法满足模拟交易闭环。

在“功能不缺失”的迁移目标下，交易域必须补齐“写路径 + 账本读路径 + 分析视图”的最小完整集。

## What Changes

- 扩展 `trading-account`：
  - 账户生命周期（创建、更新、查询）；
  - 订单生命周期（创建、填充、撤销、查询）；
  - 成交与资金流水（trade/cash-flow）查询与写入（入金/出金）；
  - 账户分析视图（overview、stats、position-summary）。
- 统一事务边界：
  - 订单成交与资金变动在同一事务边界内保持一致。

## Impact

- Affected specs:
  - `trading-account`
  - `backend-user-ownership`（间接受益）
  - `risk-control`（间接受益）
- Affected code:
  - `libs/trading_account/*`
  - `libs/platform_core/*`（错误映射与响应契约）
