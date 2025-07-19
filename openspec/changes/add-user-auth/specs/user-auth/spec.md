## ADDED Requirements

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

