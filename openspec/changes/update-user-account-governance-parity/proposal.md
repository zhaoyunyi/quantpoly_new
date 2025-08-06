## Why

当前仓库 `user-auth` 已完成注册/登录/会话基础能力，但与源项目 `users.py` 能力相比，仍缺少“用户账户治理”关键能力：

- 用户资料更新与密码变更的完整后端闭环；
- 管理员用户管理（列表、状态变更、禁用/恢复）；
- 用户等级（Level 1/Level 2）与治理审计联动。

在“允许 break，但功能不能缺失”的迁移策略下，需要将这部分能力从“可登录”升级为“可运营治理”。

## What Changes

- 扩展 `user-auth`：
  - 增加用户资料更新、密码变更、会话失效策略；
  - 增加管理员用户管理能力（列表、启用/禁用、等级调整）。
- 扩展 `admin-governance`：
  - 将用户管理动作纳入治理目录与审计日志；
  - 强制管理员动作记录 `actor/action/target/result`。
- 统一错误语义：
  - 普通用户调用管理员接口统一返回 403（含稳定错误码）。

## Impact

- Affected specs:
  - `user-auth`
  - `admin-governance`
  - `backend-user-ownership`（间接受益）
- Affected code:
  - `libs/user_auth/*`
  - `libs/admin_governance/*`
  - 组合入口中的鉴权与错误映射（后续接入）
