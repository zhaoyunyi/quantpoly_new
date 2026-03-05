# 前端应用壳库（ui_app_shell）

本目录承载前端应用壳能力，提供：

- `PublicLayout`：公开页面布局（登录/注册等）
- `AppShell`：已认证用户主布局（侧栏导航 + 内容区 + footer）
- `AuthGuard`：认证守卫（基于 `GET /users/me`，401 重定向到 `/auth/login?next=...`）
- `ErrorBoundary`：全局错误边界（route-level / app-level）
- `NAV_ITEMS`：一级导航信息架构

> 说明：`AuthGuard` 依赖 `frontend_api_client` 的 `AuthProvider/useAuth`，并要求在应用启动时完成 `configureClient({ baseUrl })` 配置。
