## MODIFIED Requirements

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

## ADDED Requirements

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
