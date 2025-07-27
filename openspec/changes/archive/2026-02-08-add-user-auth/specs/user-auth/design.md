# user-auth Design

## 目标

在新仓库中建立“后端自管”的用户系统与鉴权能力，满足：

- 前端不再承担用户数据库与会话签发职责
- 后端提供单一权威的 `get_current_user`（避免旧项目 JWT vs better-auth 的割裂）
- 支持浏览器（Cookie Session）与 CLI（Bearer token）两类客户端

## 边界与上下文

建议将 `user-auth` 作为一个独立 bounded context：

- 聚合根：`User`
- 相关实体/值对象：`Credential`（或 `PasswordHash`）、`Session`、`EmailVerificationToken`、`PasswordResetToken`
- 对外能力：Auth API、鉴权依赖、CLI

业务上下文（策略/回测/交易/风控/监控）只依赖 `userId` 与 `CurrentUser`（或最小公开用户信息），不得直接操作认证内部表结构。

## 认证协议建议

迁移目标采用“后端自管”的 session token，并保持 **单一鉴权入口**：

1) 浏览器：HTTP-only Cookie（保存 session token，优先用于 Web）
2) CLI/服务端：Authorization Bearer（携带同一类 session token）

无论使用何种携带方式，路由层统一通过 `get_current_user` 解析并返回同一类型的 `CurrentUser`。

## 兼容策略（可选）

本仓库按迁移目标 **不兼容** 旧 better-auth。若确有过渡需要：

- 必须单独建立 change（例如 `add-better-auth-compat`），在鉴权层引入兼容解析器
- 必须默认关闭，且提供明确弃用时间表

## 安全要点

- 禁止 query 参数携带 token（除非调试开关显式打开）
- 日志脱敏（token/cookie/password/api_key）
- 密码强度校验与弱口令拒绝
- 会话撤销（logout / rotate）与过期策略
