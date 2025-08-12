## Why

当前 `trading-account` 已完成订单/成交/流水与基础概览，但相较源项目交易域，仍缺少高级读模型与运维能力：账户风险指标、权益曲线、仓位分析、待处理交易与批量价格刷新等。

这部分能力决定了“可交易”到“可运营”的跃迁，是模拟交易闭环在真实运营场景下的关键补齐项。

## What Changes

- 扩展 `trading-account`：
  - 增加高级分析读模型（风险指标、权益曲线、仓位分析）；
  - 增加待处理交易视图与运营刷新入口（受治理约束）；
  - 增加账户级统计补全（含用户级聚合统计）。
- 与 `risk-control` 对齐：
  - 账户分析输出口径与风险评估字段语义一致。

## Impact

- Affected specs:
  - `trading-account`
  - `risk-control`（间接受益）
  - `admin-governance`（间接受益）
- Affected code:
  - `libs/trading_account/*`
  - `libs/risk_control/*`
  - `libs/admin_governance/*`
