## 1. 需求与合同（Spec）

- [x] 1.1 增加订单更新/删除需求 delta（含状态约束场景）
- [x] 1.2 增加单仓位查询与待处理交易查询需求 delta（含场景）
- [x] 1.3 增加 API/CLI 合同测试

## 2. Library-First 实现

- [x] 2.1 在 `TradingAccountService` 增加订单更新与删除方法
- [x] 2.2 增加 `get_position_by_symbol` 与 `list_pending_trades`
- [x] 2.3 扩展 repository（必要字段更新、状态约束）
- [x] 2.4 补齐 CLI 命令入口

## 3. API

- [x] 3.1 增加 `PATCH /trading/accounts/{accountId}/orders/{orderId}`
- [x] 3.2 增加 `DELETE /trading/accounts/{accountId}/orders/{orderId}`
- [x] 3.3 增加 `GET /trading/accounts/{accountId}/positions/{symbol}`
- [x] 3.4 增加 `GET /trading/accounts/{accountId}/trades/pending`

## 4. 验证

- [x] 4.1 运行 `pytest -q libs/trading_account/tests`
- [x] 4.2 运行 `openspec validate update-trading-order-amendment-parity --type change --strict`
