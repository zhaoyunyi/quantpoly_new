## MODIFIED Requirements

### Requirement: 信号与执行记录必须支持可持久化存储装配
信号执行上下文 MUST 支持在 postgres 模式下持久化信号与执行记录，避免重启后状态丢失。

#### Scenario: 重启后执行记录可追踪
- **GIVEN** 用户已生成并处理多个信号
- **WHEN** 服务重启并查询执行记录
- **THEN** 仍可查询到重启前执行记录
- **AND** 仅返回当前用户数据

### Requirement: 信号执行仓储必须提供 postgres 持久化适配器
信号执行上下文 MUST 提供 postgres 持久化仓储实现，并在 postgres 运行模式下持久化信号与执行记录。

#### Scenario: 信号与执行记录在重启后可追踪
- **GIVEN** 用户已生成并执行信号
- **WHEN** 服务重启后查询信号与执行记录
- **THEN** 返回重启前已提交数据
- **AND** 仅返回当前用户可访问数据
