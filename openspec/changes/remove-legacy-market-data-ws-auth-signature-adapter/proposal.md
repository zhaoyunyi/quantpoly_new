# Change: 移除 market-data WebSocket 鉴权回调 legacy 签名回退（BREAK UPDATE）

## Why

在 `market_data.api.create_router` 中，WebSocket 鉴权当前通过 `_resolve_ws_current_user` 使用 `try/except TypeError` 依次兼容多种 `get_current_user` 签名（无参 / request / websocket）。

这会导致：

- 鉴权契约不稳定，调用方难以明确应实现哪种签名；
- 错误被 runtime 回退吞噬，问题定位滞后；
- 与已完成的“跨上下文回调必须显式签名 + 关键字调用”的治理方向不一致。

## What Changes

- **BREAKING（库内 API）**：`market_data.api.create_router` 要求 `get_current_user` 显式声明 `request` 参数（`get_current_user(request)`）。
- 移除 `_resolve_ws_current_user` 中基于 `TypeError` 的多签名回退逻辑。
- 在 router 初始化时对 `get_current_user` 执行签名校验，不满足契约则 fail-fast 抛出稳定错误。

## Impact

- Affected specs:
  - `market-data`

- Affected code:
  - `libs/market_data/market_data/api.py`
  - `libs/market_data/tests/test_api*.py`
  - `apps/backend_app`（调用侧签名确认）
