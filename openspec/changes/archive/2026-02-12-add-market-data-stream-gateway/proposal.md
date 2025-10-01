## Why

当前市场数据能力以 REST 拉取为主，缺少统一的实时流网关。源架构愿景明确存在行情 WebSocket 入口，
而当前后端缺少 `/market/stream` 类订阅能力，导致策略与监控只能轮询。

## What Changes

- 在 `market-data` 上下文新增实时流网关（WS/SSE 二选一或同时支持）。
- 定义订阅协议（symbol/timeframe/channel）与鉴权语义。
- 增加连接健康、限流与退化策略（fallback polling hints）。
- 统一行情流事件 envelope，供监控/策略上下文复用。

## Impact

- 影响 capability：`market-data`
- 关联 capability：`monitoring-realtime`、`signal-execution`
- 风险：连接数与上游限频控制需要前置容量规划
