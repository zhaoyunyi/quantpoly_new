## ADDED Requirements

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
