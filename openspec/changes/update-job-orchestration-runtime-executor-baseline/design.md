## Context

`job-orchestration` 之前仅提供任务状态机与内存调度，缺少可替换执行器抽象、重启恢复策略、调度持久化与执行链路可观测字段。

## Decisions

- 引入 `JobExecutor` 契约（`submit/dispatch/callback`），并提供 `InProcessJobExecutor` 基线实现。
- 在 `Job` 聚合增加执行可观测字段：`executor_name`、`dispatch_id`、`started_at`、`finished_at`。
- 调度层新增 `SQLiteScheduler`，支持 schedule 持久化与重启恢复计数。
- `JobOrchestrationService` 引入 `recover_runtime()`：重启时将 `running` 任务标记为 `failed`，错误码固定为 `RUNTIME_RECOVERY`。

## Break Update

- CLI 新增 `transition` 与 `runtime` 子命令，`status/schedules` 输出增加 `runtime` 字段。
- API `Job` 响应新增 `executor`、`startedAt`、`finishedAt` 字段。
- `/jobs/schedules` 返回结构升级为包含 `items + runtime` 的读模型。

## Rollback Strategy

1. 回滚到变更前 commit；
2. 保留 `job_orchestration_schedule`、扩展后的 `job_orchestration_job` 列（向后兼容读取）；
3. 若需临时降级，只关闭运行时恢复开关（`auto_recover=False`）并继续使用原有状态迁移接口。
