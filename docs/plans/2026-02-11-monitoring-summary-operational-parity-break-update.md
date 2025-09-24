# monitoring-realtime 运营摘要语义对齐迁移说明（break update）

## 背景

`/monitor/summary` 已从基础监控摘要升级为运营读模型（v2），覆盖：

- 账户（accounts）
- 策略（strategies）
- 回测（backtests）
- 任务（tasks）
- 信号（signals）
- 告警（alerts）

并对齐 WebSocket `risk_alert` 推送中的计数语义，避免 REST / WS 指标口径不一致。

## break update 影响

旧调用方若仅依赖 `signals/alerts/tasks.running` 可以继续读取；
但若做严格 schema 校验，需要升级到 v2 字段。

## v2 摘要结构

```json
{
  "type": "monitor.summary",
  "generatedAt": "...",
  "metadata": {
    "version": "v2",
    "latencyMs": 3,
    "sources": {
      "accounts": "ok",
      "strategies": "ok",
      "backtests": "ok",
      "tasks": "ok",
      "signals": "ok",
      "alerts": "ok"
    }
  },
  "accounts": {"total": 0, "active": 0},
  "strategies": {"total": 0, "active": 0},
  "backtests": {"total": 0, "pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0},
  "tasks": {"total": 0, "queued": 0, "running": 0, "succeeded": 0, "failed": 0, "cancelled": 0},
  "signals": {"total": 0, "pending": 0, "expired": 0},
  "alerts": {"total": 0, "open": 0, "critical": 0},
  "degraded": {"enabled": false, "reasons": []},
  "isEmpty": true
}
```

## 口径约定

- 所有统计默认按 `userId` 过滤，避免跨用户泄漏。
- `alerts.open`：`status != resolved`。
- `alerts.critical`：`open` 告警中 `severity in {critical, high}`。
- `tasks.running`：任务编排状态为 `running` 的数量。
- `backtests.running`：回测状态为 `running` 的数量。

## WS 对齐

`risk_alert.payload.counts` 新增并对齐摘要口径：

- `openAlerts` -> `summary.alerts.open`
- `criticalAlerts` -> `summary.alerts.critical`
- `tasksRunning` -> `summary.tasks.running`

## 迁移建议

1. 前端摘要模型升级到 v2，优先使用 `metadata.version` 做分支。
2. 若依赖 WS 告警计数，切换为读取新 `counts` 三元组。
3. 处理空态时不再依赖字段缺省，统一使用 `isEmpty/degraded`。

## 回滚策略

- 若需快速回滚，可临时仅消费旧字段：`signals`/`alerts`/`tasks.running`。
- 不建议回退后端实现，避免再次出现 REST/WS 指标口径分裂。
