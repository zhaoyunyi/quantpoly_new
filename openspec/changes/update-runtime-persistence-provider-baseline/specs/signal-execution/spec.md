## ADDED Requirements

### Requirement: 信号与执行记录必须支持可持久化存储装配
信号执行上下文 MUST 支持在 sqlite 模式下持久化信号与执行记录，避免重启后状态丢失。

#### Scenario: 重启后执行记录可追踪
- **GIVEN** 用户已生成并处理多个信号
- **WHEN** 服务重启并查询执行记录
- **THEN** 仍可查询到重启前执行记录
- **AND** 仅返回当前用户数据
