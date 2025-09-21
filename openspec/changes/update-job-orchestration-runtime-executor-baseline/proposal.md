## Why

当前 `job-orchestration` 已具备任务状态机与任务类型注册能力，但执行器与调度仍以进程内内存语义为主。
这会导致重启后调度丢失、任务执行不可持续，难以满足长任务生产运行要求。

## What Changes

- 引入统一任务执行器抽象（executor contract），与现有任务状态机解耦。
- 补齐调度恢复语义：调度配置可持久化读取并在重启后恢复。
- 明确“提交-排队-执行-回写结果”的标准链路与可观测字段。
- 保留 break update 策略，不要求兼容旧的内存调度行为。

## Impact

- 影响 capability：`job-orchestration`
- 间接影响：`monitoring-realtime`、`strategy-management`、`market-data`（依赖任务执行状态）
- 风险：任务状态迁移语义变化，需要补齐跨域回归测试
