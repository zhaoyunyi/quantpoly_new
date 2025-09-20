## Why

当前策略执行相关查询能力分散在 `strategy-management` 与 `signal-execution`，存在口径分散与前端拼装风险。
需要在后端形成稳定读模型，补齐“模板按类型查询 + 按策略统计/趋势”语义。

## What Changes

- 在 `signal-execution` 收口策略执行查询读模型：
  - 模板按类型查询；
  - 按策略维度统计与趋势查询。
- 统一统计字段定义，保障与监控摘要一致。

## Impact

- 影响 capability：`signal-execution`
- 可能联动 capability：`strategy-management`、`monitoring-realtime`
