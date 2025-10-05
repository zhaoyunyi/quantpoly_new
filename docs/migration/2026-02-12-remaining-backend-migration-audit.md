# 剩余后端迁移盘点（2026-02-12，已更新）

## 1. 盘点范围

- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 对比维度：API 路由语义、任务编排语义、核心读模型能力、CLI 对应能力

## 2. 已完成能力结论

当前项目已完成后端闭环并归档的迁移能力包括：

- 用户系统后端聚合（注册/登录/会话/管理员治理/密码找回持久化）
- 行情查询与批量报价、指标任务、行情流网关（WS/REST/CLI）
- 策略管理、研究优化（grid/bayesian + budget + trials）
- 策略组合（Portfolio）聚合、读模型、评估/再平衡任务
- 任务编排统一调度与 runtime 可观测
- 风控、信号执行、交易账户、回测任务链路
- 策略列表分页/状态/关键词查询（`update-strategy-list-query-parity`）
- 市场目录详情与目录过滤（`update-market-catalog-detail-parity`）

## 3. 当前“功能不缺失”结论

> 按“可以 break update，但功能不能缺失”的原则复核后，**功能缺口已清零**。

- 之前识别的两项缺口（策略列表查询能力、市场目录详情能力）均已实现并归档。
- 兼容层清理变更 `remove-legacy-session-token-compat`、`remove-legacy-is-admin-compat` 已完成并归档（P1，非功能缺口，治理型重构）。

## 4. 可选后续工作（非缺口，按收益排序）

### 4.1 P1：兼容层清理（若彻底 break update）

- 目标：统一新路由命名与返回 envelope，清理历史兼容分支。
- 收益：降低维护成本，减少 API 文档与实现偏差。

### 4.2 P1：跨上下文查询收敛

- 目标：把跨域聚合查询沉淀为显式 read-model 服务（避免路由层拼装）。
- 收益：更符合 DDD 限界上下文与防腐层原则。

### 4.3 P2：任务编排与领域任务 SLA 分层

- 目标：按任务类型声明优先级、重试策略、并发上限与可观测指标模板。
- 收益：提高自动化任务在高负载下的稳定性和可诊断性。

## 5. 建议的下一步

1. 若继续迁移主线：进入“归档后新一轮优化”阶段，先做 `P1` 兼容层清理。
2. 若进入稳定期：冻结 OpenSpec 迁移变更，转向性能、可观测与运维治理。
