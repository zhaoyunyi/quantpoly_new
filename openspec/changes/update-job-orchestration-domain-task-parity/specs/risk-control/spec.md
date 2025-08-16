## ADDED Requirements

### Requirement: 风控巡检任务必须支持统一编排
风控批量巡检与告警处理任务 MUST 支持统一任务编排与状态追踪。

#### Scenario: 风控巡检任务可轮询状态
- **GIVEN** 用户发起风控巡检任务
- **WHEN** 系统接收并排队执行
- **THEN** 返回可轮询状态的任务句柄
- **AND** 查询结果仅限任务所属用户
