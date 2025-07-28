## ADDED Requirements

### Requirement: 用户与会话必须持久化
`user-auth` MUST 使用持久化存储管理用户与会话，服务重启后会话状态可追踪且可撤销。

#### Scenario: 服务重启后会话可验证
- **GIVEN** 用户已登录并获得有效会话 token
- **WHEN** 后端服务重启
- **THEN** 同一 token 仍可通过 `get_current_user` 验证
- **AND** 调用登出后该 token 必须失效

### Requirement: 兼容 legacy better-auth token/cookie 输入
后端 MUST 支持旧前端迁移期 token 输入格式，并统一到后端会话语义。

#### Scenario: Bearer token.signature 与 Cookie 均可识别
- **GIVEN** 请求携带 `Authorization: Bearer <token.signature>` 或 `__Secure-better-auth.session_token`
- **WHEN** 调用受保护接口
- **THEN** 后端能正确提取并验证 token 主体
- **AND** 鉴权结果与标准 `session_token` 一致

### Requirement: 支持邮箱验证与密码找回
后端 MUST 提供邮箱验证与密码找回流程，替代前端内嵌认证逻辑。

#### Scenario: 未验证邮箱登录被拒绝
- **GIVEN** 用户已注册但邮箱未验证
- **WHEN** 用户尝试登录
- **THEN** 返回可识别的业务错误码（如 `EMAIL_NOT_VERIFIED`）
- **AND** 可触发重新发送验证邮件流程

#### Scenario: 重置密码后旧凭证失效
- **GIVEN** 用户完成密码重置
- **WHEN** 使用旧密码或旧重置 token 再次登录/重置
- **THEN** 后端拒绝请求并返回安全错误响应

### Requirement: 认证日志必须脱敏请求上下文
后端 MUST 在认证日志中对 token、cookie、认证请求体进行脱敏。

#### Scenario: 鉴权失败日志不包含明文 token
- **GIVEN** 鉴权失败并写日志
- **WHEN** 日志包含 header/cookie/body 片段
- **THEN** token/cookie/password 均以掩码形式输出
- **AND** 不允许出现可直接复用的凭证明文

