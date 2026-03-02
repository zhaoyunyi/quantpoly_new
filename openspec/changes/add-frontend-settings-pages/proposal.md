# Change: 前端设置（Settings）页面（偏好/主题/账户）

## Why

设置页面用于让用户管理个人偏好、主题与账户资料，并与后端 `user-preferences` 与 `user-auth` 能力对齐，形成自助闭环（资料更新/改密/注销）。

## What Changes

- 实现路由：
  - `/settings`（偏好总览）
  - `/settings/theme`（主题偏好写入 preferences）
  - `/settings/account`（资料、密码、注销）
- 对接后端端点：
  - `GET/PATCH /users/me/preferences`
  - `POST /users/me/preferences/reset`
  - `GET /users/me/preferences/export`、`POST /users/me/preferences/import`
  - `GET/PATCH/DELETE /users/me`
  - `PATCH /users/me/password`

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/settings/*`
- Affected specs:
  - `frontend-settings`

