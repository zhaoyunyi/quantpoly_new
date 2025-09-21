## ADDED Requirements

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
