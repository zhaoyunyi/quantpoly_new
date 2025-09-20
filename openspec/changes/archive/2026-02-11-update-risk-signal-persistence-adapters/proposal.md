## Why

risk/signal 当前仍以 InMemory 为主，无法满足重启恢复、运营排障与审计追踪需求。
在 runtime 基座完成后，需要落地 risk/signal 的持久化适配器。

## What Changes

- 为 `risk-control` 与 `signal-execution` 增加 sqlite 持久化仓储。
- 在组合入口接入对应适配器并完成数据结构初始化。
- 补齐仓储级/服务级测试，验证重启后数据可恢复。

## Impact

- 影响 capability：`risk-control`、`signal-execution`
- 依赖：`update-runtime-persistence-provider-baseline`
