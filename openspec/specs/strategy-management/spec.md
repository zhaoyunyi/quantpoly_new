# strategy-management Specification

## Purpose
TBD - created by archiving change add-strategy-backtest-migration. Update Purpose after archive.
## Requirements
### Requirement: 策略 CRUD 必须按用户隔离
后端 MUST 按 `current_user.id` 约束策略的创建、读取、更新与删除。

#### Scenario: 非所有者无法读取策略详情
- **GIVEN** 策略 `strategy_id` 不属于当前用户
- **WHEN** 调用 `GET /strategies/{strategy_id}`
- **THEN** 返回 403
- **AND** 响应不暴露该策略内部字段

### Requirement: 删除策略前必须检查回测占用
后端 MUST 在删除策略前检查是否存在 `pending/running` 回测任务。

#### Scenario: 存在运行中回测时阻止删除
- **GIVEN** 目标策略存在运行中回测任务
- **WHEN** 调用 `DELETE /strategies/{id}`
- **THEN** 返回 409
- **AND** 返回占用数量与可追踪错误码

### Requirement: 策略状态变更必须持久化并在重启后可恢复
策略创建、更新、删除保护与状态变更 MUST 进入持久化路径，不得依赖 in-memory 主状态。

#### Scenario: 服务重启后策略状态可恢复
- **GIVEN** 用户已创建并更新策略状态
- **WHEN** 服务发生重启
- **THEN** 重新读取策略时必须返回重启前已提交状态
- **AND** 删除保护规则仍然生效

### Requirement: 策略必须支持模板化创建与受控状态迁移
策略管理 MUST 提供模板能力，并由领域状态机约束策略生命周期迁移。

#### Scenario: 从模板创建策略并成功激活
- **GIVEN** 用户选择一个可用策略模板
- **WHEN** 提交参数并创建策略后执行激活
- **THEN** 策略状态从 `draft` 迁移到 `active`
- **AND** 迁移过程记录参数校验结果

#### Scenario: 非法状态迁移被拒绝
- **GIVEN** 策略处于 `archived` 状态
- **WHEN** 用户尝试直接激活策略
- **THEN** 后端返回 409
- **AND** 错误码可用于前端识别状态冲突

### Requirement: 策略执行前必须通过模板参数校验
策略进入执行链路前 MUST 完成模板参数校验，避免无效策略进入下游执行系统。

#### Scenario: 未通过校验的策略禁止进入执行链路
- **GIVEN** 策略参数缺失关键字段
- **WHEN** 用户发起执行请求
- **THEN** 后端拒绝请求并返回参数校验错误
- **AND** 策略状态与执行记录保持不变

### Requirement: 策略必须支持受控更新与参数重校验
策略管理 MUST 提供更新能力，并在参数变化时执行模板约束校验。

#### Scenario: 策略更新触发参数重校验
- **GIVEN** 用户修改策略参数
- **WHEN** 调用策略更新接口
- **THEN** 系统执行模板参数校验
- **AND** 校验失败时拒绝更新并返回稳定错误码

### Requirement: 策略必须可查询关联回测视图
策略管理 MUST 提供策略维度回测列表与统计视图，用于策略研究闭环。

#### Scenario: 查询策略关联回测统计
- **GIVEN** 策略已存在多次回测任务
- **WHEN** 调用策略回测统计接口
- **THEN** 返回该策略可访问范围内的回测统计
- **AND** 不包含他人数据

### Requirement: 策略域必须支持研究自动化任务
策略管理系统 MUST 支持策略绩效分析与优化建议任务化提交，支持异步结果追踪。

#### Scenario: 提交策略绩效分析任务
- **GIVEN** 用户拥有可访问策略
- **WHEN** 提交策略绩效分析任务
- **THEN** 返回可追踪 `taskId`
- **AND** 结果仅允许策略所有者读取

#### Scenario: 提交优化建议任务并读取结果
- **GIVEN** 用户策略具备历史执行数据
- **WHEN** 提交优化建议任务并轮询完成
- **THEN** 返回结构化优化建议
- **AND** 建议结果包含生成时间与适用参数范围

### Requirement: 策略模板目录必须覆盖核心内置策略并提供参数 Schema
策略管理系统 MUST 提供内置策略模板目录，用于“零编程门槛”的策略创建与参数校验。

模板目录 MUST 至少覆盖以下模板（可按版本扩展）：

- `moving_average`
- `bollinger_bands`
- `rsi`
- `macd`
- `mean_reversion`
- `momentum`

每个模板 MUST 输出稳定字段：

- `templateId`
- `name`
- `requiredParameters`（类型、范围、描述、默认值）
- `defaults`（或等价字段，用于前端一键填充）

#### Scenario: 查询模板列表返回核心模板集合
- **GIVEN** 用户已认证
- **WHEN** 调用策略模板列表接口
- **THEN** 返回包含上述核心模板集合
- **AND** 每个模板均包含 `requiredParameters` 与默认值

#### Scenario: 从模板创建策略时进行参数校验
- **GIVEN** 用户选择一个模板并提交参数
- **WHEN** 参数缺失或超出范围
- **THEN** 后端拒绝创建并返回可识别的参数错误码
- **AND** 策略不会被创建

### Requirement: 策略研究任务必须支持参数搜索空间与优化目标
策略研究能力 MUST 支持结构化参数搜索空间、优化目标与约束条件输入，而非固定轻量建议。

#### Scenario: 提交参数搜索任务并通过校验
- **GIVEN** 用户提交策略研究任务并声明参数搜索空间
- **WHEN** 输入满足 schema 与约束条件
- **THEN** 系统接受任务并返回可追踪 `taskId`
- **AND** 任务记录包含优化目标与参数空间摘要

#### Scenario: 非法参数空间被拒绝
- **GIVEN** 用户提交参数范围冲突或字段缺失
- **WHEN** 系统校验研究任务输入
- **THEN** 返回稳定参数错误码
- **AND** 不创建任何研究任务记录

### Requirement: 策略研究结果必须可持久化查询与复算
策略研究结果 MUST 以持久化读模型形式对外提供，支持按策略查询历史结果并可追踪版本。

#### Scenario: 查询策略最近研究结果
- **GIVEN** 策略已完成多次研究任务
- **WHEN** 用户查询该策略研究结果
- **THEN** 返回按时间排序的结果列表
- **AND** 每条结果包含评分、参数建议、生成时间与关联任务标识

#### Scenario: 非所有者无法读取研究结果
- **GIVEN** 研究结果不属于当前用户策略
- **WHEN** 调用研究结果查询接口
- **THEN** 返回 403
- **AND** 不泄露研究结果内容

### Requirement: 系统必须支持策略组合聚合
策略管理上下文 MUST 提供策略组合聚合，支持在一个组合内管理多个策略成员。

#### Scenario: 创建组合并添加成员策略
- **GIVEN** 用户拥有多个策略
- **WHEN** 用户创建组合并添加成员策略
- **THEN** 系统保存组合与成员关系
- **AND** 仅允许同一用户拥有的策略加入组合

#### Scenario: 非法成员关系被拒绝
- **GIVEN** 用户尝试添加不属于自己的策略
- **WHEN** 系统校验成员归属
- **THEN** 返回权限错误
- **AND** 组合状态保持不变

### Requirement: 策略组合必须支持权重约束与再平衡任务
组合管理 MUST 提供权重约束校验与再平衡任务能力。

#### Scenario: 权重约束校验
- **GIVEN** 用户设置组合成员权重
- **WHEN** 总权重不满足约束规则
- **THEN** 返回稳定参数错误码
- **AND** 不应用该次权重更新

#### Scenario: 触发组合再平衡任务
- **GIVEN** 组合已存在有效成员和权重
- **WHEN** 用户触发再平衡任务
- **THEN** 系统返回可追踪任务标识
- **AND** 任务结果包含调仓建议与风险摘要

### Requirement: 策略研究优化必须支持网格与贝叶斯两类方法
策略研究优化 MUST 至少支持 `grid` 与 `bayesian` 两种优化方法。

#### Scenario: 网格搜索优化任务
- **GIVEN** 用户提交 method=`grid` 的优化任务
- **WHEN** 参数空间与预算合法
- **THEN** 系统执行网格 trial 并输出最优参数组合
- **AND** 返回可追踪任务标识与结果版本

#### Scenario: 贝叶斯优化任务
- **GIVEN** 用户提交 method=`bayesian` 的优化任务
- **WHEN** 参数空间、约束与预算满足要求
- **THEN** 系统基于历史 trial 迭代搜索
- **AND** 输出最优候选与收敛摘要

### Requirement: 优化结果必须包含 trial 明细与预算语义
优化结果读模型 MUST 提供 trial 级明细以及预算执行信息。

#### Scenario: 查询优化结果明细
- **GIVEN** 策略已完成优化任务
- **WHEN** 用户查询研究结果
- **THEN** 返回 trial 列表、best candidate、budget usage
- **AND** 支持按 method/status/version 过滤

#### Scenario: 预算耗尽触发早停
- **GIVEN** 任务设置了最大 trial 或时间预算
- **WHEN** 达到预算上限
- **THEN** 优化任务进入完成状态
- **AND** 结果中标记早停原因

### Requirement: 策略列表必须支持分页与条件查询
策略管理接口 MUST 支持按状态和关键词查询，并返回稳定分页结构。

#### Scenario: 按状态筛选并分页查询策略
- **GIVEN** 用户拥有多个不同状态策略
- **WHEN** 调用 `GET /strategies` 并传入 `status`、`page`、`pageSize`
- **THEN** 返回该用户范围内满足条件的分页结果
- **AND** 响应包含 `items`、`total`、`page`、`pageSize`

#### Scenario: 按关键词搜索策略名称
- **GIVEN** 用户拥有多条策略记录
- **WHEN** 调用 `GET /strategies` 并传入 `search`
- **THEN** 仅返回名称匹配关键词的策略
- **AND** 不得泄漏其他用户策略

