## Why

当前风控域已覆盖规则与评估快照，但源项目中的风险报告生成、告警通知处理、连续监控、历史告警清理与快照批处理能力尚未迁移。
缺失这些能力会导致风控停留在“手工查询”，无法形成“自动发现-通知-治理”闭环。

## What Changes

- 将风险报告、告警通知、连续监控、快照生成纳入统一任务编排。
- 补齐告警历史清理策略与审计约束。
- 对齐监控通道中风险事件通知语义。

## Impact

- Affected specs:
  - `risk-control`
  - `monitoring-realtime`
- Affected code:
  - `libs/risk_control/*`
  - `libs/monitoring_realtime/*`
  - `libs/job_orchestration/*`
