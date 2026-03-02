# Change: user-auth 增加“重发邮箱验证”端点

## Why

旧前端存在 `/auth/resend-verification` 页面，且 `openspec/specs/user-auth/spec.md` 要求“未验证邮箱登录被拒绝后可触发重新发送验证邮件流程”。当前后端未提供明确的 resend 端点，导致前端无法形成闭环。

## What Changes

- 在 `libs/user_auth/user_auth/app.py` 增加 resend 验证端点（建议：`POST /auth/verify-email/resend`）
- 端点语义：
  - 对存在且未验证用户：受理请求并返回统一成功语义
  - 对不存在用户：仍返回统一成功语义（抗枚举）
  - 开发阶段允许先以“记录审计日志 + 返回 success”作为占位，不接真实邮件服务
- 增加单元测试覆盖成功语义与抗枚举

## Impact

- Affected code:
  - `libs/user_auth/user_auth/app.py`
  - `libs/user_auth/tests/*`（新增）
- Affected specs:
  - `user-auth`（新增/补强 requirement）

