## ADDED Requirements

### Requirement: Backend MUST support CORS for frontend web origin with credentials

后端组合入口 MUST 提供可配置的 CORS 支持，使浏览器前端可在跨 Origin 调用后端 API 时携带 `session_token` cookie（credentials）。

#### Scenario: CORS preflight is accepted for allowed origin
- **GIVEN** 系统配置允许的前端 origin 列表包含 `http://localhost:3000`
- **WHEN** 浏览器对后端发起 `OPTIONS` 预检请求
- **THEN** 响应包含 `access-control-allow-origin=http://localhost:3000`
- **AND** 响应包含 `access-control-allow-credentials=true`

#### Scenario: CORS is disabled by default to avoid unexpected behavior changes
- **GIVEN** 系统未配置任何允许的前端 origin
- **WHEN** 对后端发起跨 Origin 请求
- **THEN** 后端不主动返回允许跨域的 CORS 头（保持关闭）

### Requirement: CORS errors MUST not block error readability

在认证失败（401）或权限失败（403）时，后端仍 MUST 返回正确的 CORS 响应头（当 origin 被允许时），以便前端能够读取错误码并展示给用户。

#### Scenario: Unauthorized response still includes CORS headers for allowed origin
- **GIVEN** 请求来自允许的前端 origin
- **AND** 请求未携带有效 `session_token`
- **WHEN** 调用受保护端点（如 `GET /users/me`）
- **THEN** 返回 401
- **AND** 响应仍包含 `access-control-allow-origin=<allowed origin>`
- **AND** 响应仍包含 `access-control-allow-credentials=true`

