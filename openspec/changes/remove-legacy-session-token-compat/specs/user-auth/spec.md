## REMOVED Requirements

### Requirement: 兼容 legacy better-auth token/cookie 输入
后端 MUST 支持旧前端迁移期 token 输入格式，并统一到后端会话语义。

#### Scenario: Bearer token.signature 与 Cookie 均可识别
- **GIVEN** 请求携带 `Authorization: Bearer <token.signature>` 或 `__Secure-better-auth.session_token`
- **WHEN** 调用受保护接口
- **THEN** 后端能正确提取并验证 token 主体
- **AND** 鉴权结果与标准 `session_token` 一致

## ADDED Requirements

### Requirement: 会话鉴权必须仅接受标准 token 输入
后端会话鉴权 MUST 仅接受标准 `Bearer <session_token>` 与 `session_token` Cookie 输入。

#### Scenario: legacy Bearer token.signature 被拒绝
- **GIVEN** 请求使用 `Authorization: Bearer <token.signature>`
- **WHEN** 调用受保护接口
- **THEN** 返回 `401/INVALID_TOKEN`
- **AND** 不再进行 legacy 主体截断解析

#### Scenario: legacy better-auth cookie 被拒绝
- **GIVEN** 请求仅携带 `__Secure-better-auth.session_token` 或 `better-auth.session_token`
- **WHEN** 调用受保护接口
- **THEN** 返回 `401/INVALID_TOKEN`
- **AND** 不得回退读取 legacy cookie key
