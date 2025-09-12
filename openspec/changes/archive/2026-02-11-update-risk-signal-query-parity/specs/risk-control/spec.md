## ADDED Requirements

### Requirement: 风控系统必须提供规则统计与告警快捷查询
风控系统 MUST 提供规则统计、近期告警、未解决告警的快捷查询接口，以支撑监控与运营排障。

#### Scenario: 获取规则统计
- **GIVEN** 用户已配置多条风控规则
- **WHEN** 调用规则统计接口
- **THEN** 返回规则总数与按状态统计

#### Scenario: 获取近期告警与未解决告警
- **GIVEN** 用户存在多条告警记录
- **WHEN** 调用 `recent/unresolved` 快捷接口
- **THEN** 返回对应子集告警
- **AND** 仅返回当前用户可访问数据
