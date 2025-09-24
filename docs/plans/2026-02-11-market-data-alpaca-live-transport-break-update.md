# market-data Alpaca Live Transport 迁移说明（break update）

## 背景

本次变更将 `market_data_provider=alpaca` 从“占位 transport”升级为“可运行 HTTP transport”。

同时引入以下强约束：

- 缺失 Alpaca 关键配置时 **fail-fast**（不再静默占位）
- 统一上游错误语义（401/429/timeout）
- 增强 provider 健康信息中的运行态观测字段

这属于 **break update**：历史上“配置 alpaca 但运行时占位抛错”的行为不再被接受。

## 变更点

## 1) 组合入口（backend_app）

当 `market_data_provider=alpaca` 时，组合入口会注入真实 transport：

- `AlpacaTransportConfig`
- `AlpacaHTTPTransport`
- `AlpacaProvider`

若缺失关键配置，`build_context` 将直接抛出稳定错误：

- `ALPACA_CONFIG_MISSING`

## 2) market-data CLI 运行时装配

`market-data` CLI 新增 provider/runtime 参数：

- `--provider inmemory|alpaca`
- `--alpaca-api-key`
- `--alpaca-api-secret`
- `--alpaca-base-url`
- `--alpaca-timeout-seconds`

在 `provider=alpaca` 且配置缺失时，CLI 返回标准错误 envelope，错误码为：

- `ALPACA_CONFIG_MISSING`

## 3) 统一错误映射

新增上游错误码并在 API/CLI 对齐：

- 鉴权失败：`UPSTREAM_AUTH_FAILED`
- 上游限流：`UPSTREAM_RATE_LIMITED`
- 上游超时：`UPSTREAM_TIMEOUT`

API 状态码语义：

- `UPSTREAM_RATE_LIMITED` -> `429`
- `UPSTREAM_TIMEOUT` -> `504`
- `UPSTREAM_AUTH_FAILED` -> `502`（上游凭据问题，非终端用户鉴权）

## 4) provider-health 观测增强

Alpaca provider 健康信息新增运行态字段（脱敏）：

- `transport`
- `baseUrl`
- `timeoutSeconds`
- `lastLatencyMs`
- `lastFailureCode`

## 环境变量

## backend_app

- `BACKEND_MARKET_DATA_PROVIDER`：`inmemory` / `alpaca`
- `BACKEND_ALPACA_API_KEY`
- `BACKEND_ALPACA_API_SECRET`
- `BACKEND_ALPACA_BASE_URL`（可选，默认 `https://data.alpaca.markets`）
- `BACKEND_ALPACA_TIMEOUT_SECONDS`（可选，默认 `5`）

## market-data CLI

- `MARKET_DATA_PROVIDER`：`inmemory` / `alpaca`
- `MARKET_DATA_ALPACA_API_KEY`
- `MARKET_DATA_ALPACA_API_SECRET`
- `MARKET_DATA_ALPACA_BASE_URL`
- `MARKET_DATA_ALPACA_TIMEOUT_SECONDS`

> CLI 也兼容读取 `BACKEND_ALPACA_*` 作为回退。

## 示例

### backend_app

```bash
export BACKEND_MARKET_DATA_PROVIDER=alpaca
export BACKEND_ALPACA_API_KEY=xxx
export BACKEND_ALPACA_API_SECRET=yyy
```

### market-data CLI

```bash
market-data quote \
  --user-id u-1 \
  --symbol AAPL \
  --provider alpaca \
  --alpaca-api-key xxx \
  --alpaca-api-secret yyy
```

## 回滚策略

1. 将 `BACKEND_MARKET_DATA_PROVIDER` 回退为 `inmemory`。
2. 若必须临时禁用 live provider，保留 API/CLI 接口不变，仅切换 provider。
3. 不建议回退到旧的占位 transport 行为（会造成运行时不可预测失败）。
