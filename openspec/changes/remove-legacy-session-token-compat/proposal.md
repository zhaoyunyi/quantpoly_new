## Why

当前后端仍保留 legacy better-auth token 兼容逻辑（`token.signature`、`__Secure-better-auth.session_token`、`better-auth.session_token`）。
在“允许 break update，但功能不能缺失”的迁移策略下，这类兼容分支会持续增加鉴权复杂度与误判风险。

## What Changes

- 移除 legacy better-auth token/cookie 兼容解析。
- 统一会话 token 输入约定：仅接受标准 Bearer token 与 `session_token` Cookie。
- 调整 CLI 与 WS 鉴权行为：legacy 输入统一返回 `INVALID_TOKEN/UNAUTHORIZED`。

## Impact

- 影响 capability：`user-auth`
- 连带影响：`monitoring-realtime`（复用同一 token 提取器）
- 风险：仍在发送 legacy token 的旧客户端会在升级后鉴权失败

## Break Update 迁移说明

- 不再支持：
  - `Authorization: Bearer <token.signature>` 的 legacy 主体截断
  - `__Secure-better-auth.session_token`
  - `better-auth.session_token`
- 客户端必须迁移为：
  - `Authorization: Bearer <session_token>`
  - 或 `Cookie: session_token=<session_token>`
