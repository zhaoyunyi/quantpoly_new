# Change: 前端基础库落地（API Client / UI Design System / App Shell）

## Why

前端重构将覆盖多条业务链路（策略/回测/交易/监控/设置）。如果每个页面各自直连后端、各自处理错误与样式，会导致：
- 契约不一致（分页/envelope/错误码解析分散）
- UI 风格漂移（颜色、间距、状态、可访问性难统一）
- 认证守卫重复实现（401/重定向/next 参数等不一致）

因此需要先落地“可复用基础库”，为后续各页面并行实现提供稳定底座。

## What Changes

- 落地 `libs/frontend_api_client/`：
  - 统一 `fetch` 封装（baseUrl、credentials、超时、错误映射）
  - 后端 envelope 解包（`success_response/error_response`）
  - 提供可脚本化 CLI（健康检查、接口探测，stdout 输出 JSON）
- 落地 `libs/ui_design_system/`（Base UI + Tailwind）：
  - `Button/Input/Select/Dialog/Toast/Table/Skeleton` 等最小组件集合
  - 全部样式来自 tokens（`apps/frontend_web/app/styles/app.css`）
  - 提供 tokens 导出/校验 CLI（stdout 输出 JSON）
- 落地 `libs/ui_app_shell/`：
  - `AppShell` 布局、一级导航、全局错误边界、Toast 容器
  - 认证守卫（基于 `GET /users/me`）

## Impact

- Affected code:
  - `apps/frontend_web/app.config.ts`（允许导入 `libs/*` 源码）
  - 新增 `libs/frontend_api_client/*`、`libs/ui_design_system/*`、`libs/ui_app_shell/*`
- Affected specs:
  - `frontend-api-client`
  - `frontend-ui-design-system`
  - `frontend-app-shell`

