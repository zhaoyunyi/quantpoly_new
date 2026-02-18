# job-orchestration Specification

## Purpose
为后端长任务提供统一的提交、派发、调度与状态机追踪能力（submit/dispatch/callback），确保任务幂等、用户隔离、可恢复与可观测，并作为各业务上下文异步任务的唯一入口。
## Requirements
### Requirement: 后端长任务必须通过统一任务编排能力提交
回测、行情同步、交易批处理、风险巡检、信号批处理等长任务 MUST 通过统一任务编排层提交与追踪，不得由 API 直接执行阻塞流程。

#### Scenario: 提交任务返回可追踪 taskId
- **GIVEN** 用户发起回测或批处理请求
- **WHEN** 后端接受任务
- **THEN** 返回标准 envelope，包含 `taskId` 与初始状态
- **AND** 客户端可通过任务查询接口轮询状态

### Requirement: 任务必须具备幂等与所有权隔离
任务提交与查询 MUST 显式绑定 `userId`，并支持幂等键避免重复执行。

#### Scenario: 相同幂等键重复提交不会创建重复任务
- **GIVEN** 同一用户在有效窗口内重复提交同一业务任务且携带相同 `idempotencyKey`
- **WHEN** 后端处理请求
- **THEN** 返回同一 `taskId`
- **AND** 不得重复入队执行

#### Scenario: 越权查询任务被拒绝
- **GIVEN** 任务 `taskId` 不属于当前用户
- **WHEN** 调用任务查询接口
- **THEN** 返回 403
- **AND** 不泄露任务存在性细节

### Requirement: 任务编排必须依赖持久化队列状态与唯一约束
任务提交、查询、状态迁移 MUST 基于持久化状态存储，并对 `idempotencyKey` 强制唯一约束。

#### Scenario: 并发提交任务时保持唯一与一致
- **GIVEN** 同一用户并发提交携带相同 `idempotencyKey` 的任务
- **WHEN** 系统执行任务入队
- **THEN** 仅允许一个任务创建成功
- **AND** 其余请求必须返回明确幂等冲突语义

### Requirement: 任务编排必须支持多领域异步任务类型
任务编排系统 MUST 支持回测、信号、风控、交易、策略研究、行情同步等领域任务的统一提交与状态追踪。

#### Scenario: 提交策略绩效分析任务返回 taskId
- **GIVEN** 用户发起策略绩效分析请求
- **WHEN** 系统接受任务
- **THEN** 返回 `taskId` 与初始状态
- **AND** 客户端可通过任务查询接口轮询状态

#### Scenario: 提交风险通知处理任务返回 taskId
- **GIVEN** 用户发起风险告警通知处理请求
- **WHEN** 系统接受任务
- **THEN** 返回 `taskId` 与初始状态
- **AND** 状态迁移语义与其他任务保持一致

### Requirement: 任务状态机语义必须跨领域一致
不同领域任务的状态迁移 MUST 遵循统一状态机与错误码语义。

#### Scenario: 重复幂等键提交返回同一任务语义
- **GIVEN** 同一用户重复提交相同幂等键任务
- **WHEN** 系统处理提交
- **THEN** 返回同一任务语义或明确冲突
- **AND** 不重复创建执行任务

### Requirement: 任务类型必须可注册并可查询

任务编排系统 MUST 提供任务类型注册表与查询能力，避免由业务代码散落硬编码 task type。

#### Scenario: CLI 查询任务类型注册表

- **GIVEN** 运维通过 CLI 查询任务类型
- **WHEN** 执行任务类型列表命令
- **THEN** 返回结构化任务类型清单
- **AND** 输出包含领域归属与可调度标记
- **AND** 输出 MUST NOT 包含 `legacyNames` 等迁移期兼容字段

### Requirement: 调度语义必须支持用户范围与命名空间隔离
调度配置 MUST 显式绑定用户范围与任务命名空间，禁止跨租户读取/操作调度对象。

#### Scenario: 越权读取他人调度配置被拒绝
- **GIVEN** 调度对象不属于当前用户命名空间
- **WHEN** 调用调度查询或停止接口
- **THEN** 返回 403
- **AND** 不泄露调度对象存在性细节

### Requirement: 任务编排必须具备可替换执行器语义
任务编排系统 MUST 提供独立于 API 层的执行器抽象，用于统一任务提交、分发与结果回写。

#### Scenario: 任务提交后由执行器驱动状态迁移
- **GIVEN** 用户提交一个受支持的异步任务
- **WHEN** 系统接受任务并交由执行器处理
- **THEN** 任务状态按照 `queued -> running -> succeeded|failed` 迁移
- **AND** 状态迁移不依赖 API 请求线程持续存活

#### Scenario: 执行器失败回写稳定错误语义
- **GIVEN** 执行器处理任务时发生异常
- **WHEN** 系统回写任务状态
- **THEN** 任务进入 `failed` 状态
- **AND** 返回可识别错误码与错误消息

### Requirement: 调度配置必须支持重启恢复
调度配置 MUST 可持久化并在服务重启后恢复，避免仅依赖进程内内存。

#### Scenario: 服务重启后调度配置可恢复
- **GIVEN** 用户已创建 interval 或 cron 调度
- **WHEN** 服务重启
- **THEN** 调度配置仍可查询
- **AND** 调度任务可继续按配置触发

#### Scenario: 越权用户无法恢复或操作他人调度
- **GIVEN** 调度配置不属于当前用户命名空间
- **WHEN** 调用调度恢复或停止接口
- **THEN** 返回 403
- **AND** 不泄露调度对象细节

### Requirement: 任务执行必须经过统一 dispatch 链路
所有业务任务 MUST 经由 `submit -> dispatch -> callback` 完整链路执行，不得在业务 API 内直接标记为成功。

#### Scenario: 任务提交后进入真实异步状态机
- **GIVEN** 用户提交一个可调度任务
- **WHEN** 任务被写入编排系统
- **THEN** 初始状态为 `queued`
- **AND** 任务被 dispatch 后进入 `running`
- **AND** callback 到达后进入 `succeeded` 或 `failed`

#### Scenario: 执行器异常时保持可观测失败
- **GIVEN** 执行器派发失败或回调异常
- **WHEN** 编排系统处理异常
- **THEN** 任务状态变为 `failed`
- **AND** 返回稳定错误码与可追踪执行上下文

### Requirement: 任务运行时必须支持模式化执行器与系统调度模板
任务编排运行时 MUST 支持执行器模式切换，并提供系统级调度模板注册与恢复能力。

#### Scenario: 运行时模式切换
- **GIVEN** 系统配置了执行器运行时模式
- **WHEN** 任务被 dispatch
- **THEN** 任务通过对应执行器完成派发
- **AND** 运行时状态接口返回当前执行器模式

#### Scenario: 调度模板恢复
- **GIVEN** 系统存在已注册的调度模板
- **WHEN** 服务重启并执行恢复流程
- **THEN** 调度模板被恢复为可运行状态
- **AND** 不会产生重复模板记录

### Requirement: 任务类型必须声明 SLA Policy

任务编排系统 MUST 为每个 `taskType` 声明稳定的 SLA Policy（至少包含：优先级、超时、最大重试次数、并发上限），并提供可查询输出用于门禁与运维治理。

#### Scenario: CLI 查询任务类型包含 SLA 字段

- **GIVEN** 运维需要核对系统任务治理策略
- **WHEN** 执行 `python -m job_orchestration.cli types`
- **THEN** 返回的每个任务类型包含 `priority/timeoutSeconds/maxRetries/concurrencyLimit`
- **AND** 字段命名使用 camelCase

### Requirement: 任务编排库不得再暴露 sqlite 持久化适配器
任务编排 capability MUST 不再把 sqlite 仓储作为受支持公开能力。

#### Scenario: 任务编排公开契约不包含 sqlite
- **GIVEN** 业务方通过任务编排库集成任务能力
- **WHEN** 检查公开导出与能力文档
- **THEN** 仅允许 `Postgres` 与 `InMemory` 作为可用仓储路径
- **AND** sqlite 路径不再受支持

