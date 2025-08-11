# user-auth Specification

## Purpose
用户系统（注册、登录、会话管理、权限判断）由后端统一实现与持有，并提供单一 `get_current_user` 依赖，保证 HTTP 与 WebSocket 等通道鉴权语义一致。
## Requirements
### Requirement: 用户系统能力聚合到后端
用户系统（注册、登录、会话管理、权限判断、偏好设置读写） MUST 由后端实现与持有。

#### Scenario: 前端不再直接读写用户数据库
- **GIVEN** 前端需要完成注册/登录/登出/获取当前用户
- **WHEN** 前端发起请求
- **THEN** 前端 MUST 仅调用后端 API
- **AND** 前端 MUST NOT 直接连接或迁移/操作用户数据库（如 D1/SQLite/Postgres）

### Requirement: 后端提供注册与登录
后端 MUST 提供注册与登录接口，支持浏览器与 CLI 两种客户端。

#### Scenario: 浏览器用户注册
- **GIVEN** 未登录用户提交邮箱与密码
- **WHEN** 后端完成校验并创建用户
- **THEN** 返回创建成功
- **AND** 根据配置触发邮箱验证流程（可选）

#### Scenario: CLI 用户登录
- **GIVEN** CLI 通过用户名/密码调用登录
- **WHEN** 凭证正确
- **THEN** 返回可用于后续 API 调用的访问凭证（如 Bearer token）

### Requirement: 后端提供会话查询与撤销
后端 MUST 能查询当前会话对应的用户，并能撤销会话。

#### Scenario: 获取当前用户信息
- **GIVEN** 请求携带有效访问凭证
- **WHEN** 调用 `GET /users/me`（或等价端点）
- **THEN** 返回当前用户的对外公开信息

#### Scenario: 登出撤销会话
- **GIVEN** 用户已登录
- **WHEN** 调用登出端点
- **THEN** 当前会话凭证 MUST 失效

### Requirement: 密码安全与弱口令拒绝
后端 MUST 强制最小密码强度要求，并拒绝常见弱口令。

#### Scenario: 弱口令注册被拒绝
- **GIVEN** 用户注册时提交弱口令（如 `password`）
- **WHEN** 后端执行校验
- **THEN** 返回 400/422
- **AND** 错误信息不泄漏安全策略细节（避免被枚举）

### Requirement: 认证日志与敏感信息脱敏
后端 MUST 对 token、cookie、password 等字段脱敏后再写入日志。

#### Scenario: 认证失败不泄漏 token
- **GIVEN** 认证失败
- **WHEN** 服务记录日志
- **THEN** 日志中 token/cookie 只能以“前缀+掩码”形式出现

### Requirement: 单一鉴权依赖（Single CurrentUser）
后端 MUST 提供单一 `get_current_user` 作为权威鉴权依赖，并在所有业务路由中复用。

#### Scenario: 同一 token 在所有路由一致生效
- **GIVEN** 一个有效的访问凭证
- **WHEN** 访问任意受保护业务路由
- **THEN** 鉴权结果一致（同一 userId / 权限）

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

### Requirement: 用户资料与密码变更必须由后端统一管理
后端 MUST 提供用户资料更新与密码变更接口，并在密码变更后执行会话失效策略。

#### Scenario: 用户修改密码后旧会话失效
- **GIVEN** 用户已登录并持有有效会话
- **WHEN** 用户成功修改密码
- **THEN** 旧会话 token 不再可用于访问受保护接口
- **AND** 新密码可用于重新登录

#### Scenario: 非法密码更新请求被拒绝
- **GIVEN** 用户提交不满足强度规则的新密码
- **WHEN** 后端校验请求
- **THEN** 返回 400/422
- **AND** 响应包含稳定错误码

### Requirement: 管理员必须可治理用户状态与等级
后端 MUST 提供管理员用户治理接口，用于查询用户、调整状态与等级。

#### Scenario: 普通用户访问管理员接口被拒绝
- **GIVEN** 普通用户已认证
- **WHEN** 调用 `/admin/users` 相关接口
- **THEN** 返回 403
- **AND** 不返回目标用户敏感信息

