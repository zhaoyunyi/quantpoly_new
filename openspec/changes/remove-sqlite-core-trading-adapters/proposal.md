## Why

核心交易与研究上下文（策略、回测、任务编排、交易账户）虽然运行时已走 PostgreSQL，但仍保留 sqlite 实现，造成长期双栈维护负担与行为漂移风险。

## What Changes

- 删除四个上下文的 sqlite repository 与 sqlite 相关测试；
- 统一能力契约为 `Postgres + InMemory(test double)`；
- 收敛库导出面，避免调用方继续依赖 sqlite 路径。

## Impact

- 影响 capability：`strategy-management`、`backtest-runner`、`job-orchestration`、`trading-account`
- 破坏性变更：删除 sqlite 导入路径
- 可并行性：四个上下文可并行迁移，组合测试作为最终汇合门禁
