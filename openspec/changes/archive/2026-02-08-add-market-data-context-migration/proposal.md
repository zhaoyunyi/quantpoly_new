## Why

行情数据是策略、回测、交易执行的上游依赖。源项目已有市场数据接口与 Alpaca 集成，但在当前仓库尚未形成独立可复用能力，需要按 Library-First 抽离。

## What Changes

- 新增 `market-data` capability：
  - 股票检索、实时行情、历史 K 线、技术指标查询；
  - Provider 适配层（先兼容 Alpaca）；
  - 缓存与限流策略。
- 对外提供统一 API + CLI，便于自动化验证和离线调试。

## Impact

- 新增 capability：`market-data`
- 依赖 capability：`platform-core`、`user-auth`
- 被依赖 capability：`strategy-management`、`backtest-runner`、`signal-execution`

