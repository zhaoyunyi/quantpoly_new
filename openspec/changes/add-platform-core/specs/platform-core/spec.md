## ADDED Requirements

### Requirement: 平台核心库提供统一的配置加载
平台核心库 MUST 提供统一的配置加载机制，支持从环境变量与 `.env` 文件读取，并能在不同环境（local/staging/production）下进行约束校验。

#### Scenario: local 环境允许弱配置但给出告警
- **GIVEN** 环境为 `local`
- **WHEN** 检测到 `SECRET_KEY` 为空或弱口令
- **THEN** 系统仍可启动
- **AND** 输出明确告警信息（不包含敏感值）

#### Scenario: production 环境拒绝弱配置
- **GIVEN** 环境为 `production`
- **WHEN** 检测到 `SECRET_KEY` 为空或弱口令
- **THEN** 系统 MUST 启动失败
- **AND** 错误信息不应包含敏感值

### Requirement: 平台核心库提供统一的 API 响应信封
平台核心库 MUST 提供统一的 API 响应信封（success/error/paged），并能在 FastAPI 路由中直接复用。

#### Scenario: success_response 返回一致结构
- **GIVEN** 任意业务接口执行成功
- **WHEN** 返回 `success_response(data, message)`
- **THEN** 响应体包含 `success=true`、`message`、`data`

#### Scenario: error_response 返回一致结构
- **GIVEN** 任意业务接口发生业务错误
- **WHEN** 返回 `error_response(code, message)`
- **THEN** 响应体包含 `success=false`、`error.code`、`error.message`

### Requirement: 对外 API 字段统一 camelCase
平台核心库 MUST 提供工具，将对外 API 响应字段序列化为 `camelCase`；数据库与内部模型字段 MAY 保持 `snake_case`。

#### Scenario: 响应字段自动序列化为 camelCase
- **GIVEN** 内部模型字段为 `created_at`
- **WHEN** 通过平台核心响应序列化返回
- **THEN** 客户端看到字段为 `createdAt`

### Requirement: 认证 token 在日志中必须脱敏
平台核心库 MUST 提供统一的敏感信息脱敏策略，至少覆盖：token、cookie、密码、API key。

#### Scenario: 打印认证信息时不泄漏 token
- **GIVEN** 服务记录认证失败日志
- **WHEN** 日志包含 token 相关字段
- **THEN** token 只能以固定长度前缀 + 掩码形式出现

