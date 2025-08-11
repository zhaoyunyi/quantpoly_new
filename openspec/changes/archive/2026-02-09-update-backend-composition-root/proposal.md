## Why

当前后端能力以库级入口分散存在，虽然利于独立开发与测试，但在“分波次硬切换”阶段缺少单一装配与开关点，导致：

- 切换动作分散，难以统一发布与回滚；
- 鉴权、错误信封、日志脱敏等横切能力难以统一落地；
- WebSocket 与 REST 的行为一致性难以保障。

为满足“允许 break 但功能零缺失”的迁移目标，需要建立统一后端组合入口（composition root）。

## What Changes

- 新增统一后端组合入口能力：
  - 统一挂载各 bounded context 的 REST/WS 路由；
  - 统一注入鉴权依赖、错误信封、日志脱敏策略；
  - 统一切换开关与发布入口，支持波次级硬切换。
- 约束实时监控 WebSocket 必须通过组合入口对外暴露。

## Impact

- 影响 capability：`platform-core`、`monitoring-realtime`
- 被整合 capability：`user-auth`、`user-preferences`、`strategy-management`、`backtest-runner`、`trading-account`、`market-data`、`risk-control`、`signal-execution`、`job-orchestration`
