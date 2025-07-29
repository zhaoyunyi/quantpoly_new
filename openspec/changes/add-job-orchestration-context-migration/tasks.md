## 1. 领域与抽象

- [ ] 1.1 新建 `libs/job_orchestration` 并定义任务聚合与状态机（queued/running/succeeded/failed/cancelled）
- [ ] 1.2 定义 `JobRepository` / `Scheduler` / `Dispatcher` 接口与 in-memory 测试实现
- [ ] 1.3 提供 CLI：任务提交、取消、重试、查询（JSON 输出）

## 2. 运行时适配

- [ ] 2.1 实现 Celery 适配器（保留可替换接口）
- [ ] 2.2 支持 interval/cron 调度配置与启停控制
- [ ] 2.3 首批接入 backtest/market-data 两类任务并验证行为一致性

## 3. 安全与验证

- [ ] 3.1 所有任务读写显式接收 `user_id` 并校验所有权
- [ ] 3.2 增加幂等键冲突与重复提交测试
- [ ] 3.3 运行 `pytest -q` 与 `openspec validate add-job-orchestration-context-migration --strict`

