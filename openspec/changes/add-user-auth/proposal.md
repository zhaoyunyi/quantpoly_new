# 提案：add-user-auth

## Why（为什么要做）

旧项目存在“认证协议与用户模型割裂”的问题：

- 后端同时存在 **better-auth 会话校验** 与 **JWT 登录接口**，但鉴权依赖只识别 better-auth token，导致接口行为不一致。
- 后端 `SQLModel User`（含 `hashed_password/is_active/is_superuser/full_name`）与 better-auth 的 `user/session` 表结构不匹配，容易在运行时触发 500。
- 前端承担了用户系统（better-auth + D1/SQLite + 邮件/验证），与“用户系统聚合到后端”的迁移目标冲突。

因此需要在新仓库建立 **后端自管的用户认证与会话能力**，并定义清晰的迁移与弃用路径。

## What Changes（做什么）

- 新增 `user-auth` capability 的需求定义：注册/登录/登出/会话查询/密码重置/邮箱验证（可分阶段实现）。
- 明确：用户系统与会话签发/验证必须由后端负责；前端仅作为 UI 与 API 调用方。
- 为 CLI/自动化提供非浏览器鉴权方式（Bearer token 或等价机制）。

## Impact（影响）

- 后端成为唯一身份源（single source of truth），统一 CurrentUser 类型与权限模型。
- 为后续 bounded context（策略/回测/交易/风控/监控）提供一致的鉴权依赖。

## Out of Scope（不做什么）

- 不在本变更内迁移策略/回测/交易等业务能力。
- 不兼容旧 better-auth cookie/token；旧方案视为已弃用（如确有兼容需求，必须单独建 change 并明确退场计划）。

## Risks / Open Questions（风险与待确认）

- 最终认证形态（已确定方向：后端自管用户系统，不使用 better-auth）：
  - 推荐：**数据库持久化的 opaque session token**（浏览器用 httpOnly Cookie；CLI 用 Bearer header）
  - 备选：JWT access/refresh（如需要纯无状态扩展）

> 该提案先定义“行为与安全边界”，具体实现细节在 `design.md` 与后续实现阶段确定。
