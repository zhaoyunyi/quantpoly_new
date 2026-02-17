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

### Requirement: 用户生命周期必须支持自助注销闭环
后端 MUST 提供当前用户自助注销能力，并在注销后立即失效该用户全部会话凭证。

#### Scenario: 用户自助注销后旧会话立即失效
- **GIVEN** 用户已登录并持有有效 session token
- **WHEN** 用户调用自助注销接口
- **THEN** 用户状态变更为已注销（或不可登录）
- **AND** 原有 token 访问受保护接口返回 401/403

### Requirement: 管理员必须可查询与删除单个用户
后端 MUST 提供管理员用户详情查询与删除接口，并保持稳定错误语义。

#### Scenario: 非管理员调用用户删除接口
- **GIVEN** 普通用户已认证
- **WHEN** 调用管理员用户删除接口
- **THEN** 返回 403
- **AND** 不执行任何用户状态变更

### Requirement: 管理员必须可直接开通用户账号
用户系统 MUST 提供管理员创建用户能力，支持设置初始资料与权限等级。

#### Scenario: 管理员创建用户成功
- **GIVEN** 管理员已认证
- **WHEN** 调用管理员创建用户接口并提交合法用户数据
- **THEN** 返回新建用户信息
- **AND** 用户可按配置状态进行后续登录流程

#### Scenario: 非管理员创建用户被拒绝
- **GIVEN** 普通用户已认证
- **WHEN** 调用管理员创建用户接口
- **THEN** 返回 403
- **AND** 不创建任何用户记录

### Requirement: 密码找回 token 必须持久化并单次消费
密码找回流程 MUST 使用持久化 token 存储，并保证 token 只能被消费一次且支持过期控制。

#### Scenario: 服务重启后找回 token 仍可验证
- **GIVEN** 用户已发起密码找回并收到有效 token
- **WHEN** 后端服务重启
- **THEN** token 仍可用于重置密码
- **AND** 重置成功后该 token 立即失效

#### Scenario: 重复使用同一 token 被拒绝
- **GIVEN** token 已被成功消费一次
- **WHEN** 用户再次提交同一 token
- **THEN** 返回安全错误响应
- **AND** 不允许重复重置密码

### Requirement: 密码找回请求不得返回明文 token
`/auth/password-reset/request` MUST 返回统一受控响应，不得直接泄漏明文 reset token。

#### Scenario: 请求密码找回返回统一成功语义
- **GIVEN** 用户提交邮箱发起找回
- **WHEN** 系统受理请求
- **THEN** 返回统一成功响应
- **AND** 响应中不包含 reset token 明文字段

#### Scenario: 不存在邮箱也返回抗枚举响应
- **GIVEN** 请求邮箱不存在
- **WHEN** 调用密码找回请求接口
- **THEN** 返回与存在邮箱一致的成功语义
- **AND** 系统记录审计事件用于安全追踪

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

### Requirement: user-auth 错误必须返回统一 error_response 且保留业务错误码

`user-auth` 对外 API 在发生认证/权限/业务失败时 MUST 返回 `platform_core.error_response` 结构，且业务错误码 MUST 出现在 `error.code` 字段中（不得依赖 FastAPI 默认 `detail`）。

#### Scenario: 未验证邮箱登录返回 EMAIL_NOT_VERIFIED

- **GIVEN** 用户已注册但邮箱未验证
- **WHEN** 用户尝试登录
- **THEN** 返回 403
- **AND** 响应 `error.code=EMAIL_NOT_VERIFIED`

#### Scenario: 缺少 token 访问受保护接口返回 MISSING_TOKEN

- **GIVEN** 用户未提供 Bearer token 且无 session_token cookie
- **WHEN** 调用受保护接口（如 `GET /users/me` 或等价端点）
- **THEN** 返回 401
- **AND** 响应 `error.code=MISSING_TOKEN`

### Requirement: 当前用户资料读写必须统一使用 /users/me

系统 MUST 提供单一路由语义来表示“当前用户资源（me）”，并将读取与写入统一收敛在 `/users/me` 路径下，避免 `/auth` 与 `/users` 同时承载同一资源语义。

#### Scenario: 读取当前用户使用 GET /users/me

- **GIVEN** 用户已认证
- **WHEN** 调用 `GET /users/me`
- **THEN** 返回当前用户资料

#### Scenario: 更新当前用户使用 PATCH /users/me

- **GIVEN** 用户已认证
- **WHEN** 调用 `PATCH /users/me`
- **THEN** 返回更新后的用户资料

### Requirement: 用户认证库不得再暴露 sqlite 持久化适配器
在 PostgreSQL 硬切完成后，`user-auth` capability MUST 不再将 sqlite 适配器作为公开契约的一部分。

#### Scenario: 认证库公开面仅保留 Postgres 与 InMemory
- **GIVEN** 业务方通过库公开 API 使用认证能力
- **WHEN** 检查公开导出与文档约定
- **THEN** 必须仅包含 `Postgres` 与 `InMemory` 运行路径
- **AND** sqlite 适配器路径不再属于受支持能力

