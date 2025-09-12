## Why

当前 `user-auth` 已支持自注册与管理员查询/更新/删除，但仍缺少“管理员创建用户”能力。

在 B2B 交付、批量迁移、应急开通场景下，运营侧需要后端直接开通账号并设置初始等级/角色。
如果缺少该能力，仍需依赖前端自注册流程，无法满足治理闭环。

## What Changes

- 在 `user-auth` 增加管理员创建用户接口（含初始角色/等级/状态）。
- 在 `admin-governance` 增加管理员开通用户动作审计要求。
- 补齐 API/CLI 合同测试与管理员权限测试。

## Impact

- Affected specs:
  - `user-auth`
  - `admin-governance`
- Affected code:
  - `libs/user_auth/*`
  - `libs/admin_governance/*`（审计事件对齐）
- Dependencies:
  - `backend-user-ownership`（用户资源归属与隔离规则）
