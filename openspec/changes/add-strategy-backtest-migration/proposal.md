## Why

策略与回测是量化平台核心业务能力，源项目该能力已经存在但与当前仓库未对齐，且存在跨数据库聚合、响应契约不稳定、权限边界不一致等问题。

需要在当前仓库以 DDD + Library-First 方式重建 `strategy-management` 与 `backtest-runner`，并确保与统一用户体系、所有权规则协同。

## What Changes

- 新增 `strategy-management` capability：
  - 用户维度策略 CRUD；
  - 删除前回测占用检查（运行中/排队中阻断）；
  - 策略模板与参数校验。
- 新增 `backtest-runner` capability：
  - 回测任务创建、状态机（pending/running/completed/failed）；
  - 轮询查询与结果获取；
  - 与 WebSocket 事件广播的接口契约。

## Impact

- 新增 capability：`strategy-management`、`backtest-runner`
- 依赖 capability：`user-auth`、`backend-user-ownership`、`platform-core`
- 迁移收益：建立后续 signal-execution 与 monitoring 的数据基础

