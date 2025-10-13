# Change: 监控跨上下文查询收敛为显式 Read Model（monitoring-realtime）

## Why

当前 `monitoring-realtime` 的运营摘要（`/monitor/summary`）属于典型的跨上下文聚合查询：需要汇总账户、策略、回测、任务、信号、告警等多个 bounded context 的运行状态。

现状虽已能满足功能，但摘要构建逻辑与路由实现耦合在 `monitoring_realtime/app.py` 内，导致：

- Read Model 的边界不清晰（“路由文件”同时承担了协议与聚合查询计算）
- 难以在无 FastAPI/WS 的场景下复算摘要（门禁、排障、回归）
- 未来扩展指标口径时，容易在 WS/REST 两处出现语义漂移

因此需要把跨上下文聚合查询从路由层抽离，沉淀为 `monitoring-realtime` 的显式 Read Model，并提供可复算的 CLI 入口。

## What Changes

- 在 `monitoring-realtime` 库内新增 Read Model 模块（纯函数/服务）用于构建运营摘要。
- REST 与 WS 内部统一复用该 Read Model（避免口径漂移）。
- 新增 `monitoring-realtime` CLI 子命令：从 JSON snapshot 输入复算并输出摘要（stdout JSON）。

## Impact

- Affected specs: `monitoring-realtime`
- Affected code:
  - `libs/monitoring_realtime/monitoring_realtime/app.py`
  - `libs/monitoring_realtime/monitoring_realtime/cli.py`
  - `libs/monitoring_realtime/monitoring_realtime/read_model.py`（新增）
  - `libs/monitoring_realtime/tests/test_cli.py`

非目标：不改变对外 `/monitor/summary` 与 `/ws/monitor` 协议字段语义（保持行为不变）。
