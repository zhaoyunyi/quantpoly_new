# Change: 前端回测中心（Backtests）页面

## Why

回测中心需要覆盖回测任务的创建、列表、状态跟踪、结果查看与对比能力，并与后端 `backtest-runner` + `job-orchestration` 对齐。

## What Changes

- 实现路由：
  - `/backtests`（列表/筛选/统计/提交任务）
  - `/backtests/$id`（详情/结果/相关回测）
- 对接后端端点（节选）：
  - `GET/POST /backtests`
  - `POST /backtests/tasks`（可选：走 job orchestration）
  - `GET /backtests/statistics`
  - `GET /backtests/{id}`、`GET /backtests/{id}/result`、`GET /backtests/{id}/related`
  - `POST /backtests/{id}/cancel|retry`、`PATCH /backtests/{id}/name`
  - `POST /backtests/compare`

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/backtests/*`
  - `libs/frontend_api_client/*`
- Affected specs:
  - `frontend-backtest-center`

