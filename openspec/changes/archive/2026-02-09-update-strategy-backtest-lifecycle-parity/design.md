## Context

当前策略与回测库具备最小能力，但不足以承接“参数研究→回测对比→决策”的主用户旅程。

## Goals / Non-Goals

- Goals:
  - 建立策略生命周期状态机与模板能力。
  - 提供可聚合的回测统计与多任务对比视图。
  - 统一回测任务状态与取消语义。
- Non-Goals:
  - 不在本变更内引入高级优化算法（贝叶斯/遗传）。
  - 不实现前端页面改造。

## Decisions

- Decision: 策略状态机进入领域模型，由聚合根强制状态迁移规则。
- Decision: 回测任务状态与 `job-orchestration` 保持同构（pending/running/completed/failed/cancelled）。
- Decision: 对比接口接受明确任务集合，返回统一指标结构。

## Risks / Trade-offs

- 风险：回测对比计算开销大。
  - 缓解：先支持离线聚合与缓存，再引入增量计算。
- 风险：模板参数版本不兼容。
  - 缓解：模板引入 `templateVersion` 与参数迁移器。

## Migration Plan

1. 补齐策略模板与状态机领域测试。
2. 补齐回测统计/对比读模型测试。
3. 接入任务取消与幂等提交语义。
4. 跑通 OpenSpec 严格校验与回归测试。

## Open Questions

- 回测对比默认指标集合是否固定，还是允许用户自定义？
- 策略模板是否允许用户私有化覆盖？
