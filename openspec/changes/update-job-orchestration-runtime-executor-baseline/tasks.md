## 1. 任务执行器抽象

- [ ] 1.1 定义 executor 接口（submit/dispatch/callback）及错误语义
- [ ] 1.2 为 in-process runtime 提供基线实现（可测试、可替换）
- [ ] 1.3 保持任务类型注册表与 executor 解耦

## 2. 调度恢复与状态一致性

- [ ] 2.1 为调度配置增加持久化读取与重建流程
- [ ] 2.2 定义重启恢复时的任务状态迁移策略（queued/running/failure）
- [ ] 2.3 明确幂等键冲突与重试语义

## 3. API/CLI 与可观测性

- [ ] 3.1 补齐任务执行链路的可观测字段（startedAt/finishedAt/error）
- [ ] 3.2 更新 CLI 查询输出，暴露执行器与调度恢复状态
- [ ] 3.3 文档化 break update 行为与回滚策略

## 4. 测试与验证

- [ ] 4.1 先写失败测试（Red）：重启恢复、执行回写、幂等冲突
- [ ] 4.2 完成实现并通过 `libs/job_orchestration` 相关测试
- [ ] 4.3 运行 `openspec validate update-job-orchestration-runtime-executor-baseline --strict`
