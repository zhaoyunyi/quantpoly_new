## Why

风险与信号上下文虽然运行时已切 PostgreSQL，但仍保留 sqlite 持久化实现，会持续拉高维护复杂度并造成能力边界噪音。

## What Changes

- 删除 `risk-control` 与 `signal-execution` 的 sqlite 仓储及 sqlite 测试；
- 收敛导出面，仅保留 `Postgres + InMemory(test double)`；
- 保证组合入口在 postgres 路径下能力无缺失。

## Impact

- 影响 capability：`risk-control`、`signal-execution`
- 破坏性变更：删除 sqlite 导入路径
- 依赖：应在核心交易上下文 sqlite 清理后并行或随后执行
