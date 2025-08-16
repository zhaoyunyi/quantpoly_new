## ADDED Requirements

### Requirement: 信号批处理必须支持任务化执行
信号批量执行与批量取消 MUST 支持任务化提交与状态查询。

#### Scenario: 批量执行返回任务句柄
- **GIVEN** 用户提交大批量信号执行请求
- **WHEN** 系统进入异步编排模式
- **THEN** 返回任务句柄（taskId）
- **AND** 用户可查询批处理进度与结果
