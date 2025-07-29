## Why

源项目存在完整的异步任务体系（Celery worker + beat），覆盖回测、行情同步、交易处理、风险监控、信号分析等能力：

- `quantpoly-backend/backend/app/worker/celery_app.py`
- `quantpoly-backend/backend/app/worker/tasks/*.py`

当前仓库尚未迁移这层能力，若直接迁移业务路由会导致：

- 长任务阻塞 HTTP 请求链路；
- 重试、超时、幂等等运行语义缺失；
- 任务与用户权限边界难以统一审计。

## What Changes

- 新增 `job-orchestration` capability：
  - 统一任务模型（`taskType/status/payload/userId/idempotencyKey`）；
  - 统一提交、取消、重试、查询接口；
  - 统一调度策略（interval/cron）与任务审计；
  - 运行时适配（先兼容 Celery，保留 in-memory 测试实现）。
- 为能力提供独立 CLI（JSON 输出），用于离线调度验证与回放。

## Impact

- 新增 capability：`job-orchestration`
- 依赖 capability：`platform-core`、`user-auth`
- 被依赖 capability：`backtest-runner`、`market-data`、`trading-account`、`risk-control`、`signal-execution`

