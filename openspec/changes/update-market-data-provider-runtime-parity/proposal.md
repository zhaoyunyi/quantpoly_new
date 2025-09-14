## Why

市场数据上下文已有 provider 抽象与 alpaca 适配实现，但组合入口默认仍使用 InMemory provider。
需要补齐运行时 provider 装配，确保研究/交易链路可使用真实行情。

## What Changes

- 将 market-data provider 接入运行时配置（至少 `inmemory/alpaca`）。
- 明确 provider 健康检查、错误映射与降级语义。
- 补齐 CLI 与测试场景。

## Impact

- 影响 capability：`market-data`
- 依赖：`update-runtime-persistence-provider-baseline`
