# market-data Specification

## Purpose
为策略研究、回测与交易执行提供统一的市场数据能力：标的搜索、报价、历史 K 线、指标计算与实时订阅，并对上游 provider 做缓存、限流与降级语义收敛。
## Requirements
### Requirement: 市场数据查询必须提供统一接口与错误语义
后端 MUST 提供统一的股票检索、行情与历史数据接口，并返回一致错误语义。

#### Scenario: 上游行情服务超时时返回可识别错误
- **GIVEN** 上游行情 Provider 超时
- **WHEN** 用户调用行情接口
- **THEN** 返回标准错误 envelope
- **AND** 错误码可用于前端区分重试与降级展示

### Requirement: 行情查询必须支持缓存与限流
高频行情接口 MUST 支持缓存与请求限流，以保障稳定性。

#### Scenario: 同一 symbol 短时间重复查询命中缓存
- **GIVEN** 用户短时间重复查询同一 symbol
- **WHEN** 请求命中缓存窗口
- **THEN** 后端直接返回缓存结果
- **AND** 响应中包含可观测的缓存命中标记（如 metadata）

### Requirement: 行情服务必须支持目录与批量查询
市场数据服务 MUST 提供标的目录、符号清单、批量报价与最新行情查询能力。

#### Scenario: 用户批量查询多个标的报价
- **GIVEN** 用户提交多个股票代码
- **WHEN** 调用批量报价接口
- **THEN** 返回每个标的的最新报价或明确错误状态
- **AND** 响应包含统一时间戳与来源标记

### Requirement: 行情上游异常必须有统一降级语义
当上游 Provider 超时或限流时，服务 MUST 返回可识别错误码并支持重试判断。

#### Scenario: 上游限流时返回稳定错误码
- **GIVEN** 上游 provider 触发 rate limit
- **WHEN** 用户调用行情接口
- **THEN** 返回标准错误 envelope
- **AND** 错误码标识为可重试或需退避

### Requirement: 市场数据必须支持同步任务与状态追踪
市场数据系统 MUST 支持数据同步任务化执行，提供状态追踪、失败重试与结果摘要。

#### Scenario: 提交行情同步任务并读取状态
- **GIVEN** 用户或系统触发行情同步
- **WHEN** 系统接受任务
- **THEN** 返回 `taskId` 与初始状态
- **AND** 客户端可查询同步完成结果与失败原因

### Requirement: 市场数据必须支持技术指标计算任务
市场数据系统 MUST 提供技术指标计算任务接口，支持结构化输入输出与可复算，并至少覆盖策略研究所需的常用指标集合：

- `sma`（简单移动平均）
- `ema`（指数移动平均）
- `rsi`（相对强弱指标）
- `macd`（MACD 指标）
- `bollinger`（布林带）

每个指标输出 MUST 采用统一结构：

- `name`: 指标名（小写）
- `status`: `ok|unsupported|insufficient_data`
- `value`: 数值（仅当 `status=ok` 时必须存在）
- `metadata`: 参数回显（如 `period/stdDev/fast/slow/signal`）

#### Scenario: 计算 RSI 指标并返回数值
- **GIVEN** 系统存在标的的足量历史价格数据
- **WHEN** 用户提交 `rsi(period=14)` 指标计算任务
- **THEN** 返回 `status=ok` 且包含 `value`
- **AND** 输出包含 `metadata.period=14`

#### Scenario: 不支持的指标返回 unsupported
- **GIVEN** 用户提交未知指标名
- **WHEN** 系统执行指标计算
- **THEN** 对应指标输出 `status=unsupported`
- **AND** 响应 envelope 仍保持成功结构（由 `status` 表达不支持）

#### Scenario: 历史数据不足返回 insufficient_data
- **GIVEN** 系统历史数据长度不足以计算目标指标
- **WHEN** 用户提交指标计算任务
- **THEN** 对应指标输出 `status=insufficient_data`
- **AND** 不返回 `value` 字段

### Requirement: 行情 Provider 必须支持运行时可配置装配
市场数据上下文 MUST 支持通过运行时配置选择 provider（至少支持 `inmemory` 与 `alpaca`），并向上层暴露一致错误语义。

#### Scenario: 选择 alpaca provider 并成功装配
- **GIVEN** 运行时配置 `market_data.provider=alpaca`
- **WHEN** 组合入口启动并创建市场数据服务
- **THEN** 市场数据服务使用 alpaca provider
- **AND** `provider-health` 能返回对应 provider 标识

#### Scenario: provider 装配失败返回统一错误
- **GIVEN** provider 初始化失败（如配置缺失）
- **WHEN** 服务处理市场数据请求
- **THEN** 返回统一错误 envelope
- **AND** 错误码可用于区分配置错误与上游错误

### Requirement: 市场数据运行时必须支持真实 Provider 装配
市场数据上下文 MUST 支持在运行时装配真实行情 provider（如 alpaca），并保持与 inmemory provider 一致的接口契约。

#### Scenario: 运行时切换到 alpaca provider
- **GIVEN** 配置 `market_data.provider=alpaca`
- **WHEN** 服务启动并提供行情查询
- **THEN** 查询链路使用 alpaca provider
- **AND** 返回结构与 inmemory provider 保持一致契约

#### Scenario: provider 配置非法时拒绝启动
- **GIVEN** 配置了不支持的 provider 名称
- **WHEN** 服务启动
- **THEN** 服务启动失败并返回可识别错误
- **AND** 不得静默回退到其他 provider

### Requirement: Alpaca Provider 必须具备可运行 transport 实现
当配置 `provider=alpaca` 时，市场数据服务 MUST 使用可运行的 transport 调用链路，不得使用占位抛错实现。

#### Scenario: 配置合法时 alpaca 查询可用
- **GIVEN** 系统已配置合法 alpaca 访问参数
- **WHEN** 用户调用 quote 或 history 接口
- **THEN** 请求通过 alpaca transport 执行
- **AND** 返回统一市场数据响应结构

#### Scenario: 配置缺失时启动或请求 fail-fast
- **GIVEN** provider 设置为 alpaca 但关键配置缺失
- **WHEN** 服务启动或处理请求
- **THEN** 返回稳定可识别错误
- **AND** 不得静默回退为 inmemory 数据

### Requirement: Market Data CLI 必须支持真实 provider 装配
`market_data` CLI MUST 支持通过参数/环境变量装配真实 provider，并保持与 API 相同错误语义。

#### Scenario: CLI 在 alpaca 超时场景返回统一错误码
- **GIVEN** CLI 使用 alpaca provider
- **WHEN** 上游请求超时
- **THEN** CLI 输出标准错误 envelope
- **AND** 错误码与 API 行为一致

### Requirement: 市场数据必须提供统一实时流网关
市场数据上下文 MUST 提供统一实时流订阅入口，用于输出实时行情事件。

#### Scenario: 建立订阅并接收行情事件
- **GIVEN** 用户已通过鉴权并请求订阅指定 symbol
- **WHEN** 实时流连接建立成功
- **THEN** 服务持续推送该 symbol 的行情事件
- **AND** 事件包含统一 envelope 字段（type/symbol/timestamp/payload）

#### Scenario: 非法订阅被拒绝
- **GIVEN** 用户请求订阅非法 channel 或超出限制
- **WHEN** 服务校验订阅请求
- **THEN** 返回稳定错误码
- **AND** 不创建无效订阅

### Requirement: 实时流必须具备退化与健康可观测能力
实时流服务 MUST 暴露连接健康状态，并在上游异常时提供退化语义。

#### Scenario: 上游流异常时进入退化模式
- **GIVEN** 上游行情流短时不可用
- **WHEN** 流网关检测到异常
- **THEN** 连接状态标记为 `degraded`
- **AND** 输出可恢复建议（例如轮询回退提示）

### Requirement: 市场资产目录必须支持单资产详情查询
市场数据服务 MUST 提供按 `symbol` 查询资产详情的能力。

#### Scenario: 查询单资产详情成功
- **GIVEN** 资产目录中存在目标 symbol
- **WHEN** 调用资产详情接口
- **THEN** 返回标准化资产详情字段
- **AND** 字段缺失时按约定返回缺省值

#### Scenario: 查询不存在 symbol
- **GIVEN** 目录中不存在目标 symbol
- **WHEN** 调用资产详情接口
- **THEN** 返回稳定的 not found 错误码
- **AND** 不返回 provider 内部错误细节

### Requirement: 资产目录查询必须支持过滤条件
市场数据目录查询 MUST 支持按市场与资产类别过滤。

#### Scenario: 按 market 过滤目录
- **GIVEN** 目录存在多市场资产
- **WHEN** 调用目录查询并传入 `market`
- **THEN** 返回满足条件的资产集合
- **AND** 响应保留总量信息用于前端分页/加载策略

