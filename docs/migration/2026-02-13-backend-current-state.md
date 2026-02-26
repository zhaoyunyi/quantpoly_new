# 后端当前实现状态（2026-02-13）

> 本文档是迁移后的**实现事实**说明，仅记录与当前代码一致的状态。

## 1. 总体结论

- 后端存储主路径已统一为 **PostgreSQL + InMemory（测试/本地）**。
- 运行时代码已移除 sqlite 适配器导出与实现。
- 用户系统能力已聚合到后端（认证/会话/偏好/管理员治理）。
- OpenSpec 当前无活跃变更，规格与实现状态已收敛。

## 2. 关键能力现状（与代码对应）

### 2.1 组合入口与存储装配

- 组合入口：`apps/backend_app/router_registry.py`
- 存储模式：`postgres` / `memory`
- 配置入口：`apps/backend_app/settings.py`、`apps/backend_app/cli.py`

### 2.2 用户系统（后端聚合）

- 用户认证与会话：`libs/user_auth/user_auth/app.py`
- 用户偏好：`libs/user_preferences/user_preferences/api.py`
- 当前用户资源主路径：`/users/me`（`/auth/me` 已为移除提示）

### 2.3 核心业务上下文

- 策略：`libs/strategy_management/`
- 回测：`libs/backtest_runner/`
- 任务编排：`libs/job_orchestration/`
- 交易账户：`libs/trading_account/`
- 风控：`libs/risk_control/`
- 信号执行：`libs/signal_execution/`
- 行情与流网关：`libs/market_data/`
- 实时监控：`libs/monitoring_realtime/`

## 3. 治理门禁现状

### 3.1 能力门禁

- CLI：`python -m platform_core.cli capability-gate`
- 输入示例：`docs/gates/examples/capability_gate_input.json`

### 3.2 存储契约防回流门禁

- CLI：`python -m platform_core.cli storage-contract-gate`
- 默认校验核心库 `__all__` 导出中是否回流 sqlite 标识。

## 4. 与代码一致性说明

以下内容不再作为当前实现依据：

- 历史“剩余迁移盘点/设计稿/执行计划”文档；
- 未落地的未来波次拆分提案。

当前以 `openspec/specs/` + 本文档 + `docs/runbooks/` 为准。
