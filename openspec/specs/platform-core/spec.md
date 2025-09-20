# platform-core Specification

## Purpose
提供 QuantPoly 后端的基础库能力：统一配置加载与安全校验、统一 API 响应信封、对外字段 camelCase 序列化，以及日志中敏感信息（token/cookie/password/API key 等）脱敏；作为后续各 bounded context 的公共依赖。
## Requirements
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

### Requirement: 迁移波次必须通过能力等价门禁
在允许 breaking change 的迁移策略下，每个 Wave 在切换前 MUST 通过能力等价门禁，验收对象是“功能能力”而非旧接口兼容性。

#### Scenario: Wave 切换前执行能力等价检查
- **GIVEN** 一个待切换的迁移波次
- **WHEN** 运行该波次能力矩阵检查
- **THEN** 用户旅程与上下文能力条目必须全部通过
- **AND** 任一关键能力缺失时必须阻断切换

### Requirement: 能力门禁失败必须触发回滚流程
当波次切换后出现能力退化或严重异常，系统 MUST 按预定义流程回滚并恢复上一个稳定能力集。

#### Scenario: 切换后发现关键能力退化
- **GIVEN** 某波次切换已完成
- **WHEN** 在观察窗口内发现关键能力失败或越权风险
- **THEN** 必须触发回滚并恢复到切换前稳定版本
- **AND** 生成回滚审计记录用于后续复盘

### Requirement: 后端必须提供单一组合入口
系统 MUST 提供单一后端组合入口来装配所有 bounded context 的 REST 与 WS 能力，作为发布、切换、回滚的唯一控制点。

#### Scenario: 通过单一入口装配全部上下文
- **GIVEN** 系统存在多个已迁移上下文能力
- **WHEN** 启动后端服务
- **THEN** 所有对外 API 与 WS 能力必须由统一组合入口装配并对外可用
- **AND** 不得要求调用方分别连接多个分散入口

### Requirement: 组合入口必须统一横切策略
组合入口 MUST 统一鉴权、错误信封与日志脱敏策略，避免上下文之间出现语义漂移。

#### Scenario: 不同上下文返回一致错误语义
- **GIVEN** 两个不同业务上下文发生权限错误
- **WHEN** 客户端请求被拒绝
- **THEN** 错误响应结构与脱敏日志行为必须一致
- **AND** 不得泄露明文 token/cookie 等敏感字段

### Requirement: 组合入口必须按配置装配持久化与行情 Provider
后端组合入口 MUST 根据运行时配置装配持久化适配器与市场数据 Provider，不得在生产场景隐式回退为 InMemory。

#### Scenario: sqlite 模式装配持久化适配器
- **GIVEN** `storage_backend=sqlite`
- **WHEN** 组合入口启动并装配上下文
- **THEN** 风控、信号、偏好等上下文使用可持久化适配器
- **AND** 不得隐式使用 InMemory 作为静默降级

#### Scenario: 非法 provider 配置启动失败
- **GIVEN** 运行时配置声明了不支持的 `market_data.provider`
- **WHEN** 组合入口启动
- **THEN** 系统启动失败并返回可识别错误
- **AND** 错误信息不得泄露敏感配置值

