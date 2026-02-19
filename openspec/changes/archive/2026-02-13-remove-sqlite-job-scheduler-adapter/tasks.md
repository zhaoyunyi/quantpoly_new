## 1. 调度层 sqlite 适配器移除

- [x] 1.1 删除 `job_orchestration.scheduler.SQLiteScheduler` 实现
- [x] 1.2 删除/替换 sqlite 调度持久化测试
- [x] 1.3 增加公开契约测试，防止 sqlite 调度器回流

## 2. 验证

- [x] 2.1 运行 `libs/job_orchestration/tests` 与 `tests/composition`
- [x] 2.2 运行全量 `pytest`
- [x] 2.3 运行 `openspec validate remove-sqlite-job-scheduler-adapter --strict`
