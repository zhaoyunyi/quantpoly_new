## Why

源项目行情域包含检索、批量行情、标的目录、历史/最新数据等能力；当前仓库 `market-data` 仅保留搜索/单标的行情/历史数据基础接口。

同时，源项目还提供监控摘要 REST 与实时监控通道协同。当前仓库 `monitoring-realtime` 以 WS 为主，缺少与业务读模型联动的摘要能力。

## What Changes

- 扩展 `market-data`：
  - 标的目录与符号清单查询；
  - 批量报价、最新行情接口；
  - Provider 健康状态与降级语义。
- 扩展 `monitoring-realtime`：
  - 增加监控摘要 REST 读模型；
  - 与 WS 订阅通道统一消息语义与权限过滤。

## Impact

- Affected specs:
  - `market-data`
  - `monitoring-realtime`
  - `platform-core`（错误语义统一，间接受益）
- Affected code:
  - `libs/market_data/*`
  - `libs/monitoring_realtime/*`
