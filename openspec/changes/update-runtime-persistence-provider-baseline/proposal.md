## Why

当前组合入口在 `storage_backend=sqlite` 场景下，仍对 `risk-control`、`signal-execution`、`user-preferences` 使用 InMemory 仓储，并默认注入 InMemory 行情 Provider。该状态会导致：

- 服务重启后关键状态丢失（告警、信号执行历史、偏好）；
- 行情链路缺乏真实运行时 provider，研究与交易结果可信度不足；
- 组合入口虽然统一，但“配置可控装配”未落地，难以支撑后续并行迁移。

Wave5 需要先补齐运行时基座，再并行推进交易命令入口、执行读模型等功能迁移。

## What Changes

- 为组合入口补齐“按配置装配”能力：
  - `storage_backend` 决定持久化适配器选择（至少覆盖 `memory/sqlite`）；
  - `market_data.provider` 决定行情 provider 选择（至少覆盖 `inmemory/alpaca`）。
- 明确并约束以下上下文在 sqlite 场景的持久化语义：
  - `risk-control`
  - `signal-execution`
  - `user-preferences`
- 补充运行时配置错误的启动失败语义（fail fast），避免 silent fallback。

## Impact

- 影响 capability：`platform-core`、`market-data`、`risk-control`、`signal-execution`、`user-preferences`
- 影响代码路径：`apps/backend_app/*` 及上述上下文的 repository/store 装配层
- 该变更是后续 Wave5 并行迁移的依赖基座
