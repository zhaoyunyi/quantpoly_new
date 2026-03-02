# Change: 前端策略管理（Strategies）全链路页面

## Why

策略管理是 QuantPoly 的核心入口之一，需要覆盖策略生命周期（创建/编辑/激活/停用/归档/删除）、模板与参数、关联回测与研究任务等能力，并与后端 `strategy-management`、`backtest-runner`、`signal-execution` 等上下文对齐。

## What Changes

- 实现路由：
  - `/strategies`（列表/搜索/筛选/分页/创建）
  - `/strategies/$id`（详情/编辑/状态变更/关联回测）
  - `/strategies/simple`（向导式创建）
  - `/strategies/advanced`（高级分析入口）
  - `/strategies/compare`（多策略对比，基于回测对比）
- 对接后端端点（节选）：
  - `GET /strategies/templates`
  - `GET/POST /strategies`
  - `GET/PUT/DELETE /strategies/{id}`
  - `POST /strategies/{id}/activate|deactivate|archive`
  - `GET/POST /strategies/{id}/backtests`、`GET /strategies/{id}/backtest-stats`
  - `GET /strategies/{id}/research/results`、`POST /strategies/{id}/research/*-task`

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/strategies/*`
  - `libs/frontend_api_client/*`（策略相关 endpoints）
  - `libs/ui_design_system/*`（表格/表单/对话框）
- Affected specs:
  - `frontend-strategy-management`

