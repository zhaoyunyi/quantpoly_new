# user-auth Design

## 目标

在新仓库中建立“后端自管”的用户系统与鉴权能力，满足：

- 前端不再承担用户数据库与会话签发职责
- 后端提供单一权威的 `get_current_user`
- 支持浏览器（Cookie Session）与 CLI（Bearer token）两类客户端

## 边界与上下文

`user-auth` 作为独立 bounded context：

- 聚合根：`User`
- 值对象：`Credential`
- 实体：`Session`
- 对外能力：Auth API、鉴权依赖、CLI

业务上下文（策略/回测/交易/风控/监控）只依赖 `userId` 与 `CurrentUser`（或最小公开信息），不得直接操作认证内部表结构。

## 认证协议

迁移目标采用“后端自管”的 session token，并保持单一鉴权入口：

1. 浏览器：HTTP-only Cookie（`session_token`）
2. CLI/服务端：Authorization Bearer（同类 session token）

路由层统一通过 `get_current_user` 解析并返回同一类型的当前用户对象。

## 安全要点

- 禁止 query 参数携带 token（除非调试开关显式打开）
- 认证失败日志必须脱敏（token/cookie/password）
- 密码强度校验与弱口令拒绝
- 会话撤销（logout）与过期策略
