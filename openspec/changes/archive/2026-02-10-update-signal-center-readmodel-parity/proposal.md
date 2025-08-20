## Why

当前信号域已具备批处理与执行读模型，但源项目中的信号中心能力（详情、过期迁移、筛选搜索、账户仪表板）尚未完全补齐。
这会削弱“信号发现 -> 处置 -> 监控”的运营闭环。

## What Changes

- 补齐信号详情与过期状态迁移接口。
- 补齐 pending/expired/filter/search 读模型能力。
- 补齐账户维度统计与仪表板接口，并与监控摘要口径对齐。

## Impact

- Affected specs:
  - `signal-execution`
  - `monitoring-realtime`
- Affected code:
  - `libs/signal_execution/*`
  - `libs/monitoring_realtime/*`
  - `apps/backend_app/router_registry.py`
