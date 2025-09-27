## Why

产品需求与用户研究路径包含“多策略组合构建”，但当前后端仅支持单策略管理与研究。
缺少组合聚合、权重约束、再平衡与组合级绩效评估能力。

## What Changes

- 在策略管理上下文新增“策略组合（Portfolio）”聚合。
- 支持组合创建、策略纳入/移除、权重分配与约束校验。
- 新增组合评估与再平衡任务接口。
- 增加组合读模型（组合收益、回撤、相关性摘要）。

## Impact

- 影响 capability：`strategy-management`
- 关联 capability：`backtest-runner`、`risk-control`、`trading-account`
- 风险：组合与单策略指标口径需统一，避免跨域语义冲突
