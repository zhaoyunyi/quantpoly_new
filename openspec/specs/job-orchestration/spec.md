# job-orchestration Specification

## Purpose
TBD - created by archiving change add-job-orchestration-context-migration. Update Purpose after archive.
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

