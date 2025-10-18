# Change: 移除剩余 legacy 回调签名适配（BREAK UPDATE）

## Why

当前仓库已完成 Wave0~Wave7 的后端能力迁移并进入治理阶段（允许 break update，但功能不能缺失）。

在迁移过程中，为了兼容“旧版跨上下文回调/适配器签名”，部分服务层实现了 `try/except TypeError` 的多签名调用回退（例如仅传 `strategy_id`、仅传 `symbol` 等）。这类兼容分支会带来：

- **越权风险放大**：当回调允许省略 `user_id` 时，容易在未来演进中出现隐式全局查询；
- **契约不稳定**：同一逻辑可能以不同参数组合运行，排障困难；
- **维护成本高**：每次重构都要保留“旧签名路径”，与 break update 治理目标冲突。

因此需要一次明确的治理型 break update：收敛跨上下文回调协议为单一权威签名，移除所有 legacy 回退。

## What Changes

- **BREAKING（库内 API）**：跨上下文回调（如 backtest linkage / strategy reader / market history reader / risk reader）统一要求显式传入 `user_id` 与资源标识（如 `strategy_id/account_id/symbol`），并以关键字参数调用。
- 移除服务层内部的 `TypeError` 兼容回退逻辑（不再尝试用旧签名调用）。
- 当回调签名不满足要求时，系统以**稳定错误**拒绝启动或拒绝执行（避免静默降级）。

## Impact

- Affected specs:
  - `backend-user-ownership`

- Affected code (预期):
  - `libs/strategy_management/strategy_management/service.py`
  - `libs/backtest_runner/backtest_runner/service.py`
  - `libs/signal_execution/signal_execution/service.py`
  - `libs/trading_account/trading_account/service.py`
  - 相关单元测试与 CLI 构造默认 service 的位置

- Affected clients:
  - 任何在本仓库内构造上述服务并传入“旧签名回调”的代码，需要同步更新回调签名。
