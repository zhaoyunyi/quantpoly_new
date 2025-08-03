## Why

源项目的用户系统职责仍散落在前端（better-auth 实例、D1 绑定、认证 API 路由、token 获取与缓存、middleware），导致：

- 用户系统未真正“后端聚合”；
- 鉴权体系 JWT / better-auth 双轨并存，语义不一致；
- 多端（HTTP / WebSocket / CLI）鉴权规则难以统一；
- 安全治理难度增加（日志脱敏、会话撤销、审计追踪）。

当前仓库已有 `user-auth`、`user-preferences` 基础能力，但仍缺少持久化会话、兼容迁移、邮箱验证与密码找回等关键能力。

## What Changes

- 升级 `user-auth`：
  - 引入持久化 `UserRepository` / `SessionStore`（替代 in-memory）；
  - 统一 `get_current_user` 鉴权入口（HTTP/WebSocket/CLI 一致）；
  - 增加 legacy token 兼容（`token.signature`、`__Secure-better-auth.session_token`、`better-auth.session_token`）；
  - 新增邮箱验证、密码找回与重置流程。
- 升级 `user-preferences`：
  - 对齐偏好契约版本与响应 envelope；
  - 明确服务端 merge 语义，去除前端“本地优先兜底”带来的数据漂移。
- 完成前端职责下沉约束：
  - 前端仅保留 UI 与 API 调用，不再承担用户数据库/会话签发/权限判断逻辑。

## Impact

- 影响 capability：`user-auth`、`user-preferences`
- 影响代码范围：`libs/user_auth`、`libs/user_preferences`、`libs/platform_core`
- 安全收益：统一 token 脱敏、统一会话撤销、减少前端敏感逻辑
- 迁移收益：为后续 strategy/trading/risk/signal/monitoring 迁移提供稳定鉴权基座

