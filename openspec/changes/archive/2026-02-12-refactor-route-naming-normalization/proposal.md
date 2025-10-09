## Why

当前后端对外路由整体已具备 bounded context 顶层前缀（如 `/market`、`/risk`、`/trading`），但 `user-auth` 存在“同一资源多前缀”的不一致：

- `GET /auth/me`（读取当前用户）
- `PATCH /users/me`（更新当前用户）

这会增加客户端心智负担，也让 spec/docs 难以给出单一权威路径。

## What Changes

- 将“用户资源”相关接口统一收敛到 `/users/...`：
  - `GET /users/me` 成为读取当前用户的权威端点
  - 允许在 break update 策略下移除 `/auth/me`
- `auth` 前缀保留给认证流程：register/login/logout/verify/password-reset。
- 以本次 user-auth 规范化为样例，后续若要扩展到其他上下文，再按 bounded context 拆分 change。

## Impact

- 影响 capability：`user-auth`
- **BREAKING**：客户端若调用 `/auth/me` 需要迁移至 `/users/me`。

