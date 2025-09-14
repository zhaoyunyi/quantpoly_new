## ADDED Requirements

### Requirement: 信号执行仓储必须提供 sqlite 持久化适配器
信号执行上下文 MUST 提供 sqlite 持久化仓储实现，并在 sqlite 运行模式下持久化信号与执行记录。

#### Scenario: 信号与执行记录在重启后可追踪
- **GIVEN** 用户已生成并执行信号
- **WHEN** 服务重启后查询信号与执行记录
- **THEN** 返回重启前已提交数据
- **AND** 仅返回当前用户可访问数据
