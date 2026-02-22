# frontend-app-shell Specification

## Purpose
TBD - created by archiving change add-frontend-foundation-libraries. Update Purpose after archive.
## Requirements
### Requirement: Frontend MUST provide an authenticated App Shell with route guard

前端 MUST 提供统一 `AppShell`（侧栏导航 + 内容区），并对受保护路由实施认证守卫。

#### Scenario: Unauthenticated user is redirected to login
- **GIVEN** 用户未登录或会话已失效
- **WHEN** 访问受保护路由（如 `/dashboard`）
- **THEN** 前端跳转到 `/auth/login?next=/dashboard`

#### Scenario: Authenticated user can access protected routes
- **GIVEN** 用户已登录且 `GET /users/me` 返回 success
- **WHEN** 访问 `/dashboard`
- **THEN** 前端渲染 AppShell 与页面内容

