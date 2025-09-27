## Why

当前任务编排虽然具备 `executor` 抽象，但业务域 API 仍普遍使用“提交后立即成功”的同步路径，
与源项目 Celery/Redis 的异步执行语义不一致，无法支撑长任务、故障恢复与真实调度。

## What Changes

- 将任务执行链路统一为 `submit -> dispatch -> callback transition`，替代域 API 内部即时 `succeed`。
- 增加运行时模式配置（如 `inprocess` / `celery-adapter`），并统一执行器健康观测字段。
- 增加系统级调度模板（交易/风控/策略/信号）注册与恢复语义。
- 对外状态语义收敛：明确 `queued/running/succeeded/failed/cancelled` 生命周期边界。

## Impact

- 影响 capability：`job-orchestration`
- 关联 capability：`trading-account`、`risk-control`、`signal-execution`、`strategy-management`、`market-data`、`backtest-runner`
- 风险：旧“即时成功”调用方可能需要适配异步状态轮询与超时策略
