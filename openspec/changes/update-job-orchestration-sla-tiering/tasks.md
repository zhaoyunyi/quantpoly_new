## 1. 规格与模型

- [ ] 1.1 增补 `job-orchestration` spec：任务类型必须声明 SLA Policy
- [ ] 1.2 定义 SLA Policy 字段与默认分层（interactive/batch/maintenance 等）

## 2. 运行时治理

- [ ] 2.1 dispatch 过程增加并发上限守卫（按 userId + taskType）
- [ ] 2.2 为超时/重试策略预留可观测字段（不强制一次性做完重试机制）

## 3. CLI 与可观测

- [ ] 3.1 CLI `types` 输出包含 SLA 字段（priority/timeout/maxRetries/concurrencyLimit）
- [ ] 3.2 输出字段命名遵循统一 API 命名规范（camelCase）

## 4. 测试与验证

- [ ] 4.1 Red：CLI types 输出包含 SLA 字段
- [ ] 4.2 Red：并发上限守卫触发时任务保持 queued 且返回稳定错误码
- [ ] 4.3 Green：实现 SLA Policy 与运行时守卫
- [ ] 4.4 运行 `pytest libs/job_orchestration/tests`
- [ ] 4.5 运行 `openspec validate update-job-orchestration-sla-tiering --strict`
