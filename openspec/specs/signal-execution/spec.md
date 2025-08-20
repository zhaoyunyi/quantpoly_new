# signal-execution Specification

## Purpose
TBD - created by archiving change add-risk-signal-context-migration. Update Purpose after archive.
## Requirements
### Requirement: 信号与执行记录接口必须强制用户范围
信号查询、批处理、执行记录查询与取消 MUST 在服务端强制按当前用户过滤。

#### Scenario: 越权 signal_id 执行被拒绝
- **GIVEN** 信号不属于当前用户
- **WHEN** 调用执行或取消接口
- **THEN** 返回 403
- **AND** 信号状态不得发生变更

### Requirement: 维护类接口不得进行全局删除/更新
清理过期信号、清理旧执行记录等维护接口 MUST 限定用户作用域或仅限管理员角色。

#### Scenario: 普通用户调用全局清理接口
- **GIVEN** 普通用户已认证
- **WHEN** 调用清理接口
- **THEN** 返回 403
- **AND** 不应删除其他用户数据

### Requirement: 信号必须支持筛选搜索与批处理执行
信号执行系统 MUST 提供筛选、搜索、批量执行、批量取消能力，并保持用户隔离。

#### Scenario: 用户批量执行信号
- **GIVEN** 用户提交一组属于自己的待执行信号 ID
- **WHEN** 调用批量执行接口
- **THEN** 返回每个信号的执行结果
- **AND** 他人信号不得被执行

### Requirement: 维护类接口必须受治理约束
清理过期信号与全局维护接口 MUST 受管理员权限与审计约束。

#### Scenario: 普通用户调用全局维护接口
- **GIVEN** 普通用户已认证
- **WHEN** 调用全局清理接口
- **THEN** 返回 403
- **AND** 不执行任何删除或更新副作用

### Requirement: 策略执行控制面必须覆盖生成到处理闭环
信号执行系统 MUST 提供参数校验、信号生成、单条处理与执行详情查询能力。

#### Scenario: 参数校验失败阻断信号生成
- **GIVEN** 用户提交不满足模板约束的策略参数
- **WHEN** 调用信号生成前校验接口
- **THEN** 返回 400/422 与稳定错误码
- **AND** 不创建任何执行记录

### Requirement: 执行读模型必须支持运行中与趋势分析
执行系统 MUST 提供运行中执行列表、策略维度统计与趋势视图。

#### Scenario: 查询运行中执行列表
- **GIVEN** 用户存在 `pending/running` 执行记录
- **WHEN** 调用运行中执行查询接口
- **THEN** 返回仅属于当前用户的执行记录
- **AND** 每条记录包含状态与最近更新时间

### Requirement: 信号全局维护接口必须采用统一管理员判定策略
信号系统的全局清理/维护接口 MUST 使用统一管理员判定策略，避免角色语义漂移。

#### Scenario: 管理员执行全局清理
- **GIVEN** 当前用户具备管理员权限
- **WHEN** 调用全局清理接口
- **THEN** 请求通过并返回清理结果
- **AND** 审计日志记录动作与判权依据

### Requirement: 信号生命周期必须支持详情与过期状态迁移
信号系统 MUST 提供信号详情读取与过期状态迁移能力。

#### Scenario: 信号过期迁移后不可执行
- **GIVEN** 信号已超过过期时间
- **WHEN** 系统执行过期迁移
- **THEN** 信号状态变为 `expired`
- **AND** 后续执行请求被拒绝

### Requirement: 信号中心必须提供筛选搜索与账户仪表板
信号系统 MUST 提供 pending/expired 筛选、搜索与账户维度统计仪表板。

#### Scenario: 查询账户信号仪表板
- **GIVEN** 账户存在多个状态的信号
- **WHEN** 调用仪表板接口
- **THEN** 返回按状态聚合的信号统计
- **AND** 不包含其他用户账户数据

### Requirement: 信号批处理必须支持任务化执行
信号批量执行与批量取消 MUST 支持任务化提交与状态查询。

#### Scenario: 批量执行返回任务句柄
- **GIVEN** 用户提交大批量信号执行请求
- **WHEN** 系统进入异步编排模式
- **THEN** 返回任务句柄（taskId）
- **AND** 用户可查询批处理进度与结果

