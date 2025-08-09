## Why

当前多处上下文仍以 in-memory 仓储作为主要运行路径，不满足“硬切换后功能零缺失”的稳定性要求，主要风险包括：

- 服务重启后关键状态丢失（任务、账户、策略、回测等）；
- 并发与重试场景缺少事务一致性保障；
- 幂等提交缺少持久化唯一约束，存在重复执行风险。

因此需要引入持久化适配器与统一事务单元（Unit of Work）作为默认主路径。

## What Changes

- 在核心上下文中引入持久化 repository adapter（PostgreSQL/D1 按边界分配）；
- 引入 Unit of Work 统一事务边界；
- 对任务与关键写路径引入幂等键约束与冲突语义；
- 将 in-memory 保留为测试替身而非生产主路径。

## Impact

- 影响 capability：`trading-account`、`strategy-management`、`backtest-runner`、`job-orchestration`
- 依赖 capability：`data-topology-boundary`、`platform-core`、`backend-user-ownership`
- 间接受益 capability：`risk-control`、`signal-execution`、`monitoring-realtime`
