## Why

虽然运行时已硬切 PostgreSQL，但 `user_auth` 与 `user_preferences` 仍保留 sqlite 适配器与 sqlite 测试，形成双实现维护成本与语义漂移风险。

## What Changes

- 移除 `user_auth` 的 sqlite 仓储/会话/密码重置实现及对应测试；
- 移除 `user_preferences` 的 sqlite store 与对应测试；
- 将相关库公开 API 面统一为 `Postgres + InMemory(test double)`。

## Impact

- 影响 capability：`user-auth`、`user-preferences`
- 破坏性变更：删除 sqlite 导入路径
- 可并行性：可与核心交易 sqlite 清理并行，但需在组合测试统一收敛
