## Why

当前系统已支持 `market_data_provider=alpaca` 配置，但组合入口与 CLI 的默认 transport 仍为占位实现，实际运行会直接失败。
这导致“真实行情 provider 可运行装配”尚未真正闭环。

## What Changes

- 引入可运行的 alpaca transport 适配层（HTTP 调用、鉴权、超时与重试配置）。
- 在组合入口与 CLI 统一 provider 装配策略（inmemory/alpaca）。
- 补齐 provider 健康检查、配置缺失 fail-fast 与错误映射。
- 保持 break update：不再支持“配置 alpaca 但运行时静默占位”的行为。

## Impact

- 影响 capability：`market-data`
- 关联模块：`apps/backend_app`、`libs/market_data`
- 风险：引入外部依赖与网络波动，需要明确重试与熔断边界
