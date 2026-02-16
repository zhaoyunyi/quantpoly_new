## MODIFIED Requirements

### Requirement: 风控状态必须支持可持久化存储装配
风控上下文 MUST 支持在 postgres 模式下使用持久化仓储，保证规则、告警、快照在服务重启后可恢复。

#### Scenario: 重启后仍可读取已存在告警
- **GIVEN** 用户已有已写入的风险告警与规则数据
- **WHEN** 服务重启后再次查询
- **THEN** 可读取重启前数据
- **AND** 查询范围仍受用户隔离约束

### Requirement: 风控仓储必须提供 postgres 持久化适配器
风控上下文 MUST 提供 postgres 持久化仓储实现，并在 postgres 运行模式下作为默认写入路径。

#### Scenario: 告警与规则在重启后可恢复
- **GIVEN** 用户已有风控规则与告警记录
- **WHEN** 服务重启后再次查询
- **THEN** 返回重启前已提交数据
- **AND** 查询权限边界保持不变
