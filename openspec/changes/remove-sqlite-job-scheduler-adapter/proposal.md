## Why

当前代码仍保留 `job_orchestration.scheduler.SQLiteScheduler`，与已确立的“运行时仅 `Postgres + InMemory`”方向不一致，且增加额外维护噪音。

## What Changes

- 移除 `job_orchestration.scheduler.SQLiteScheduler` 适配器实现；
- 移除对应 sqlite 调度持久化测试；
- 补充公开契约测试，确保调度层不再暴露 sqlite 适配器。

## Impact

- 影响 capability：`job-orchestration`
- 破坏性变更：删除 `job_orchestration.scheduler.SQLiteScheduler` 导入路径
- 兼容策略：本次为 hard-cut break update，无兼容层
