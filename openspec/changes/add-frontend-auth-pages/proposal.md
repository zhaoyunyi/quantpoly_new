# Change: 前端认证与账户链路页面（Auth）

## Why

前端需要实现用户注册/登录/登出/邮箱验证/密码找回等基础能力，且必须完全依赖后端 `user-auth` 能力（cookie session + 标准错误码），以满足仓库“用户系统聚合到后端”的约束。

## What Changes

- 在 `apps/frontend_web` 增加 Auth 路由与页面：
  - `/auth/login`
  - `/auth/register`
  - `/auth/forgot-password`
  - `/auth/reset-password`
  - `/auth/verify-email`
  - `/auth/resend-verification`
- UI 统一使用 `libs/ui_design_system` 组件；数据调用统一使用 `libs/frontend_api_client`
- 处理 `next` 重定向参数与 401/403 错误展示（如 `EMAIL_NOT_VERIFIED`）

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/auth/*`
  - `libs/frontend_api_client/*`（新增 endpoint 封装）
  - `libs/ui_design_system/*`（表单组件/Toast）
- Affected specs:
  - `frontend-auth`

