## Context

交易域是平台“模拟交易”能力的核心。当前仅有读侧基础视图，缺少订单与账本生命周期，导致无法形成可回放、可审计、可统计的交易闭环。

## Goals / Non-Goals

- Goals:
  - 建立订单/成交/流水的完整生命周期。
  - 保证账本一致性与可追溯性。
  - 提供账户统计与概览读模型。
- Non-Goals:
  - 不在本变更中实现真实券商下单。
  - 不引入复杂撮合引擎（仅保留模拟成交语义）。

## Decisions

- Decision: `TradeOrder` 作为聚合根，显式状态机（pending/filled/cancelled/failed）。
- Decision: `TradeRecord` 与 `CashFlow` 作为账本事件，必须保留不可变审计字段。
- Decision: 入金/出金/成交导致资金变更统一走服务层事务边界。

## Risks / Trade-offs

- 风险：并发成交导致账户余额竞争。
  - 缓解：仓储层引入悲观/乐观锁策略与幂等键。
- 风险：统计视图与底层账本延迟不一致。
  - 缓解：优先实时聚合，必要时引入异步读模型刷新。

## Migration Plan

1. 先补齐订单状态机与领域测试。
2. 再补齐仓储与服务写路径（下单/撤单/成交/入金/出金）。
3. 最后补齐读侧（订单详情、成交列表、流水、统计概览）。
4. 完成 API/CLI 契约与 OpenSpec 校验。

## Open Questions

- 出金是否需要冻结资金流程（pending withdrawal）？
- 撤单后是否允许自动重建新订单（同参数）？
