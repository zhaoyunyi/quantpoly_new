## ADDED Requirements

### Requirement: Frontend MUST use a single API client ACL for backend access

前端 MUST 通过单一 `frontend_api_client`（ACL）访问后端公开 API，禁止页面/组件内直接拼接 URL 与自行解析响应。

#### Scenario: Route code uses typed client instead of raw fetch
- **GIVEN** 任意页面需要访问后端接口（例如 `GET /users/me`）
- **WHEN** 工程师实现页面数据拉取
- **THEN** 代码仅通过 `frontend_api_client` 调用
- **AND** 页面中不出现直接 `fetch('http://...')` 形式的后端调用

### Requirement: API client MUST support cookie session via credentials

API client MUST 在浏览器请求中启用 `credentials: include`，以携带后端签发的 `session_token` cookie。

#### Scenario: Authenticated request carries session cookie
- **GIVEN** 用户已通过 `POST /auth/login` 登录且浏览器已保存 `session_token` cookie
- **WHEN** 前端调用 `GET /users/me`
- **THEN** 浏览器请求携带 cookie
- **AND** 后端返回当前用户资料

### Requirement: API client MUST map backend error_response into stable AppError

API client MUST 将后端 `error_response` 与网络异常映射为稳定 `AppError`，供 UI 统一展示与处理。

#### Scenario: Unauthorized maps to auth-kind error
- **GIVEN** 用户未登录
- **WHEN** 调用受保护端点（如 `GET /users/me`）
- **THEN** API client 返回 `AppError.kind=auth`
- **AND** `AppError.code` 来自后端 `error.code`

