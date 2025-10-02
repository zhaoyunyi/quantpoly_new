# 剩余后端迁移盘点（2026-02-12）

## 1. 盘点范围

- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 对比维度：API 路由语义、任务编排语义、核心读模型能力、CLI 对应能力

## 2. 已完成能力结论

以下能力在当前项目已具备后端闭环，并已进入 OpenSpec 归档：

- 用户系统后端聚合（注册/登录/会话/管理员治理/密码找回持久化）
- 行情查询与批量报价、指标任务、行情流网关（WS/REST/CLI）
- 策略管理、研究优化（grid/bayesian + budget + trials）
- 策略组合（Portfolio）聚合、读模型、评估/再平衡任务
- 任务编排统一调度与 runtime 可观测
- 风控、信号执行、交易账户、回测任务链路

## 3. 仍建议补齐的迁移项（功能不缺失导向）

> 说明：已按“break update 可接受，但功能不能缺失”的原则筛选。

### 3.1 策略列表查询能力补齐（建议 P0）

源项目策略列表支持分页/状态/搜索；当前项目策略列表仍是“按用户全量返回”。

- 风险：前端列表在策略量增大后体验下降，且状态筛选需要在前端二次处理。
- 建议迁移：补齐 `status/search/page/pageSize` 查询语义，后端统一分页输出。

### 3.2 市场资产目录详情能力补齐（建议 P1）

源项目存在“按 symbol 查询资产详情（stocks/{symbol}）”语义；当前项目提供 catalog/search/quote/history，但缺少显式“资产详情读模型端点”。

- 风险：前端资产详情页需要拼接多接口，语义分散。
- 建议迁移：新增 `catalog/{symbol}` 详情能力 + 可选市场过滤（market/assetClass）。

## 4. 依赖与并行关系

- `update-strategy-list-query-parity`：仅影响 `strategy-management`，可独立实施。
- `update-market-catalog-detail-parity`：仅影响 `market-data`，可独立实施。
- 两项互不依赖，可**并行推进**。

## 5. 下一步执行建议

1. 先按 OpenSpec 评审并确认优先级（建议先做 P0）。
2. 每条变更按 TDD 执行：Red（API+CLI）→ Green → 回归。
3. 完成后按 `git cnd` 提交，并进入归档流程。
