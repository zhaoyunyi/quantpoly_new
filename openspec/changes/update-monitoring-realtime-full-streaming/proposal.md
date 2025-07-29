## Why

当前仓库 `monitoring-realtime` 仅覆盖最小心跳与鉴权，尚未迁移源项目中真实监控能力（signals/alerts 增量推送、频道订阅、消息 envelope 约定）。

该能力依赖 risk/signal/trading 数据，因此应独立成后置变更，避免与核心迁移耦合。

## What Changes

- 扩展 `monitoring-realtime`：
  - 标准消息 envelope（`type/payload/data/timestamp`）；
  - 频道订阅管理（`subscribe/unsubscribe`）；
  - `signals_update` 与 `risk_alert` 按用户权限推送；
  - 心跳 `ping/pong` 与断线恢复约定。
- 强化 WebSocket 鉴权日志脱敏，避免 header/cookie 泄漏。

## Impact

- 修改 capability：`monitoring-realtime`
- 依赖 capability：`signal-execution`、`risk-control`、`trading-account`、`user-auth`
- 用户价值：监控面板从“可连通”升级为“可运营”

