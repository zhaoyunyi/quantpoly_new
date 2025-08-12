## Why

源项目用户域除注册/登录外，还覆盖“用户自助注销 + 管理员用户销毁”的生命周期闭环；当前仓库 `user-auth` 已具备资料更新与管理员状态治理，但缺少**账户删除链路**。

在“功能不缺失”的迁移目标下，用户域需补齐 destructive action 的治理与审计，避免形成“可创建不可退出、可禁用不可销毁”的运维缺口。

## What Changes

- 扩展 `user-auth`：
  - 新增用户自助注销（删除/停用）能力；
  - 新增管理员用户详情与删除能力；
  - 删除后执行会话失效与凭证清理。
- 扩展 `admin-governance`：
  - 用户删除动作纳入治理动作目录与审计日志。

## Impact

- Affected specs:
  - `user-auth`
  - `admin-governance`
- Affected code:
  - `libs/user_auth/*`
  - `libs/admin_governance/*`
