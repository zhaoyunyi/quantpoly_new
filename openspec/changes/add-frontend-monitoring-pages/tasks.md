## 1. `/monitor` 页面结构

- [ ] 1.1 首屏加载：`GET /monitor/summary`
- [ ] 1.2 三块区域（可响应式）：Signals / Alerts / Tasks(or Summary)
- [ ] 1.3 显示 degraded 状态与原因（来源于 summary）

## 2. WebSocket 对接（直连后端）

- [ ] 2.1 连接 `WS /ws/monitor`（依赖 cookie session）
- [ ] 2.2 连接成功后发送：
  - [ ] `subscribe`（channels: `signals`, `alerts`）
  - [ ] 定时 `ping`，处理 `pong`
- [ ] 2.3 处理消息：
  - [ ] `monitor.heartbeat`
  - [ ] `signals_update`（snapshot/增量）
  - [ ] `risk_alert`（snapshot）
- [ ] 2.4 断线重连：指数退避；超过阈值后降级为轮询（`poll`/REST）

## 3. Signals 读与操作闭环

- [ ] 3.1 列表与筛选：`GET /signals`、`GET /signals/search`、`GET /signals/pending`
- [ ] 3.2 单项操作：
  - [ ] `POST /signals/{signal_id}/process`
  - [ ] `POST /signals/{signal_id}/execute`
  - [ ] `POST /signals/{signal_id}/cancel`
- [ ] 3.3 批量操作（可选）：
  - [ ] `POST /signals/batch/execute`
  - [ ] `POST /signals/batch/cancel`

## 4. Alerts 读与操作闭环

- [ ] 4.1 列表：`GET /risk/alerts?unresolvedOnly=true`
- [ ] 4.2 统计：`GET /risk/alerts/stats`
- [ ] 4.3 单项操作：
  - [ ] `PATCH /risk/alerts/{alert_id}/acknowledge`
  - [ ] `POST /risk/alerts/{alert_id}/resolve`
- [ ] 4.4 批量 ack（可选）：`POST /risk/alerts/batch-acknowledge`

## 5. 组件规划

- [ ] 5.1 `MonitorConnectionBadge`（connected/degraded/offline）
- [ ] 5.2 `SignalList` + `SignalRowActions`
- [ ] 5.3 `AlertList` + `AlertRowActions`
- [ ] 5.4 `OperationalSummaryBar`

## 6. 测试（TDD）

- [ ] 6.1 单元测试：WS 消息 `signals_update` 触发列表更新
- [ ] 6.2 单元测试：断线后进入降级状态提示

## 7. 回归验证

- [ ] 7.1 `cd apps/frontend_web && npm run build`
- [ ] 7.2 `pytest -q`

