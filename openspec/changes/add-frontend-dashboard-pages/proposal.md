# Change: 前端仪表盘（Dashboard）页面

## Why

仪表盘是用户登录后的第一落点，需要聚合展示账户/策略/回测/告警等关键状态，符合 `spec/UISpec.md` 的“结论优先原则”。

## What Changes

- 新增受保护路由 `/dashboard`
- 使用后端现有 read model / 统计端点聚合数据：
  - `GET /monitor/summary`
  - `GET /trading/accounts/aggregate`
  - `GET /backtests/statistics`
  - （可选）`GET /risk/alerts/stats`、`GET /signals/dashboard`
- UI 使用 `libs/ui_design_system`，数据使用 `libs/frontend_api_client`

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/dashboard/*`
- Affected specs:
  - `frontend-dashboard`

