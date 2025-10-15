# Change: 任务编排 SLA 分层与可观测策略（job-orchestration）

## Why

当前 `job-orchestration` 已完成 `submit -> dispatch -> callback` 的真实异步链路，但在“运行时治理”层面仍存在两个短板：

1. **所有任务同质化**：缺少按任务类型的优先级、并发上限、超时与重试策略，导致高价值交互任务可能被批处理/维护任务挤占资源。
2. **可观测口径不统一**：不同领域在任务失败/重试/限流上的语义与指标口径容易分叉，难以形成稳定的运维与门禁策略。

为满足产品愿景中的“可持续运行 + 可诊断”的后端能力，需要把 SLA（服务等级目标）从隐式约定升级为**显式模型与可查询策略**。

## What Changes

- 在 `job-orchestration` 的 `task_registry` 中为每个 `taskType` 增加 **SLA Policy**（至少包含：`priority`、`timeoutSeconds`、`maxRetries`、`concurrencyLimit`）。
- `dispatch_job` / `scheduler` 在可实现范围内**优先遵循 SLA Policy**（例如：并发上限守卫、超时语义与可观测输出）。
- CLI `types` 输出中增加 SLA 字段，用于门禁验证与运维巡检。

> 第一阶段默认采用“**taskType 维度的静态 SLA**”（不引入用户级动态配置），避免过早引入复杂配置系统。

## Impact

- Affected specs: `job-orchestration`
- Affected code (expected):
  - `libs/job_orchestration/job_orchestration/task_registry.py`
  - `libs/job_orchestration/job_orchestration/service.py`
  - `libs/job_orchestration/job_orchestration/cli.py`
  - `libs/job_orchestration/tests/*`

风险与非目标：
- 非目标：本变更不强制引入 Celery/Redis/K8s 等运行时，仅在现有执行器抽象内实现最小可治理能力。
