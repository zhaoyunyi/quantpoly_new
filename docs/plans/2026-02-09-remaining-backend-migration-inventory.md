# 2026-02-09 剩余后端功能迁移盘点与 OpenSpec 拆分

## 1. 盘点目标与约束

- 目标：对源项目 `claude-code/quantpoly` 的后端能力做“剩余迁移”盘点，并给出按依赖/可并行性的 OpenSpec 拆分。
- 约束：
  - 允许 break（不做接口兼容迁移）。
  - 但功能能力不能缺失（能力等价）。
  - 用户系统必须后端聚合，前端仅作为 UI/API 调用方。
  - 遵循 `spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`。

## 2. 产品愿景与需求文档对齐结论

结合源项目文档 `docs/需求分析最终版本.md` 与 `docs/项目实施计划文档.md`，产品核心不是“接口兼容”，而是以下能力闭环：

1. **策略研究闭环**：策略模板/参数管理 → 回测任务 → 结果分析/对比。
2. **模拟交易闭环**：账户资金/持仓/订单/成交/流水 → 风险评估 → 监控。
3. **可控与可治理**：用户分层（Level1/Level2）、权限治理、审计、告警。
4. **数据与实时性**：行情检索/批量行情/历史数据 + 实时监控通道。

结论：当前仓库已完成上下文骨架迁移，但与产品愿景相比，仍存在“业务能力深度不足”的缺口，尤其在交易账本、策略回测分析、风险信号批处理、用户管理治理四个维度。

## 3. 源/目标能力差异（按后端路由规模快速量化）

> 说明：此处是静态扫描数量级对比，用于排序，不等同于质量评估。

- 源项目（`quantpoly-backend/backend/app/api/routes`）
  - `trading.py`: 25
  - `risk_control.py`: 19
  - `signals.py`: 18
  - `strategy_execution.py`: 15
  - `users.py`: 12
  - `strategies.py`: 11
  - `trading_accounts.py`: 10
  - `backtests.py`: 10
  - `market_data.py`: 8
- 当前项目（`libs/*/*/api.py`）
  - `signal_execution`: 7
  - `user_preferences`: 5
  - `trading_account`: 4
  - `strategy_management`: 4
  - `risk_control`: 3
  - `market_data`: 3
  - `backtest_runner`: 3

结论：剩余能力主要集中在“业务读写深度与管理治理能力”，不是基础框架问题。

## 4. 当前后端架构合理性审查（基于 DDD + Library-First）

### 4.1 合理部分

- 已按 bounded context 拆库（`libs/*`），方向正确。
- 用户认证/偏好已后端化，符合“用户系统后端聚合”目标。
- OpenSpec 工作流存在，且已形成能力规格基线。

### 4.2 需要调整的部分

1. **能力覆盖偏“骨架化”**：多数上下文仅覆盖核心 happy-path，缺少完整业务生命周期。
2. **组合入口尚未统一收口**：`composition root` 仍在进行中，横切能力（鉴权/错误码/脱敏）尚未全局一致。
3. **持久化与事务边界未全面落地**：多个上下文仍以 in-memory 为主路径，不满足硬切换稳定性。
4. **任务编排与业务上下文耦合关系未固化**：长任务提交、幂等、回滚语义在上下文间尚不统一。
5. **治理面不足**：管理员动作、用户分层能力（Level）在能力规格里仍需补齐到可执行场景。

## 5. 剩余迁移功能拆分（按依赖与可并行）

## 5.1 依赖主链（串行）

- Wave 0（前置基座）：
  - `add-capability-baseline-gates`（进行中）
  - `update-backend-composition-root`（进行中）
  - `update-persistence-adapters-uow`（进行中）
- Wave 1（业务深度补齐）：可并行执行（A/B/C）
- Wave 2（高耦合联动）：在 Wave 1 基本完成后推进（D/E）

## 5.2 可并行工作包

- **A（用户治理）**：`update-user-account-governance-parity`
- **B（策略回测）**：`update-strategy-backtest-lifecycle-parity`
- **C（交易账本）**：`update-trading-order-ledger-parity`
- **D（风险信号）**：`update-risk-signal-governance-parity`（依赖 B/C）
- **E（行情与可观测）**：`update-market-data-observability-parity`（可与 D 并行但依赖 Wave 0）

## 6. 本次新建 OpenSpec 变更（建议执行顺序）

1. `update-user-account-governance-parity`
2. `update-strategy-backtest-lifecycle-parity`
3. `update-trading-order-ledger-parity`
4. `update-risk-signal-governance-parity`
5. `update-market-data-observability-parity`

## 7. 关键风险与缺陷关注点

1. **越权风险回归**：迁移时必须默认“所有接口都要显式 user_id 过滤”。
2. **错误语义漂移**：必须统一 envelope 与 error_code，避免前端逻辑分叉。
3. **账本一致性风险**：交易订单/成交/资金流水必须保证可追溯与事务一致。
4. **批处理幂等风险**：批量执行与维护任务必须具备 idempotency key 与冲突语义。
5. **监控泄漏风险**：WS/监控摘要必须做用户权限过滤与敏感字段脱敏。

## 8. 结论

- 当前项目方向正确，但要达成“可 break 但功能不缺失”，必须从“上下文骨架”进入“业务能力深度补齐”。
- 本文已将剩余迁移拆为 5 个可管理 OpenSpec 变更，并给出依赖与并行路径。
- 下一步建议：先并行推进 A/B/C，再在其结果上执行 D/E。
