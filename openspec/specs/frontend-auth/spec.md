# frontend-auth Specification

## Purpose
TBD - created by archiving change add-frontend-auth-pages. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL provide login and register pages backed by user-auth

前端 SHALL 提供 `/auth/login` 与 `/auth/register`，并仅通过后端 `user-auth` 接口完成认证流程。

#### Scenario: Successful login redirects to dashboard or next
- **GIVEN** 用户输入有效邮箱与密码
- **WHEN** 前端调用 `POST /auth/login`
- **THEN** 后端设置 `session_token` cookie
- **AND** 前端跳转到 `next`（若存在）否则跳转 `/dashboard`

#### Scenario: Email not verified shows actionable error
- **GIVEN** 用户邮箱未验证
- **WHEN** 用户尝试登录
- **THEN** 前端展示 `EMAIL_NOT_VERIFIED` 提示
- **AND** 提供跳转到 `/auth/verify-email` 与 `/auth/resend-verification` 的入口

### Requirement: Frontend SHALL provide password reset flow

前端 SHALL 提供密码找回与重置页面，并对接后端密码找回接口。

#### Scenario: Request password reset always shows non-enumerating success message
- **GIVEN** 用户在 `/auth/forgot-password` 输入邮箱
- **WHEN** 调用 `POST /auth/password-reset/request`
- **THEN** 前端展示统一成功语义（不暴露邮箱是否存在）

#### Scenario: Confirm password reset with token
- **GIVEN** 用户从重置链接进入 `/auth/reset-password?token=...`
- **WHEN** 提交新密码并调用 `POST /auth/password-reset/confirm`
- **THEN** 前端展示成功提示并引导重新登录

