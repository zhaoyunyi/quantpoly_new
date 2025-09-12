## Why

当前 `trading-account` 已覆盖账户、下单、成交、流水与统计主链路，但与源项目后端相比仍缺少“订单维护 + 快捷查询”能力：

- 缺少订单更新/删除（撤单语义）接口；
- 缺少按标的查询单仓位能力；
- 缺少账户维度待处理交易快捷视图。

这些能力属于模拟交易运营闭环中的高频动作，缺失会降低交易控制和排障效率。

## What Changes

- 增加订单维护能力：订单更新（受限字段）与删除/撤销。
- 增加账户查询能力：按 `symbol` 获取单仓位、获取账户待处理交易列表。
- 补齐 API/CLI 合同测试与状态机约束测试（仅允许在可编辑状态更新/删除）。

## Impact

- Affected specs:
  - `trading-account`
- Affected code:
  - `libs/trading_account/*`
- Dependencies:
  - `risk-control`（下单前风控语义保持一致）
