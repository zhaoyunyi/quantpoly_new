## ADDED Requirements

### Requirement: 风控仓储必须提供 sqlite 持久化适配器
风控上下文 MUST 提供 sqlite 持久化仓储实现，并在 sqlite 运行模式下作为默认写入路径。

#### Scenario: 告警与规则在重启后可恢复
- **GIVEN** 用户已有风控规则与告警记录
- **WHEN** 服务重启后再次查询
- **THEN** 返回重启前已提交数据
- **AND** 查询权限边界保持不变
