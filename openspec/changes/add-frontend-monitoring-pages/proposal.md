# Change: 前端实时监控（Monitor）页面（WS 直连）

## Why

实时监控用于观察信号与告警、任务运行状态，并提供最小的操作闭环（ack/resolve、signal process/execute/cancel）。该页面是“运行态”体验的核心。

## What Changes

- 实现路由 `/monitor`
- 直连后端 WebSocket：`/ws/monitor`
- 同时使用 REST 端点做首屏与降级：
  - `GET /monitor/summary`
  - `GET /signals/*`
  - `GET /risk/alerts*`
- UI 使用 `libs/ui_design_system`，并实现断线重连与降级策略

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/monitor/*`
- Affected specs:
  - `frontend-monitoring`

