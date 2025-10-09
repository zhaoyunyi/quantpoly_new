## ADDED Requirements

### Requirement: user-auth 错误必须返回统一 error_response 且保留业务错误码

`user-auth` 对外 API 在发生认证/权限/业务失败时 MUST 返回 `platform_core.error_response` 结构，且业务错误码 MUST 出现在 `error.code` 字段中（不得依赖 FastAPI 默认 `detail`）。

#### Scenario: 未验证邮箱登录返回 EMAIL_NOT_VERIFIED

- **GIVEN** 用户已注册但邮箱未验证
- **WHEN** 用户尝试登录
- **THEN** 返回 403
- **AND** 响应 `error.code=EMAIL_NOT_VERIFIED`

#### Scenario: 缺少 token 访问受保护接口返回 MISSING_TOKEN

- **GIVEN** 用户未提供 Bearer token 且无 session_token cookie
- **WHEN** 调用受保护接口（如 `GET /users/me` 或等价端点）
- **THEN** 返回 401
- **AND** 响应 `error.code=MISSING_TOKEN`

