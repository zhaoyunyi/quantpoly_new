## ADDED Requirements

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
