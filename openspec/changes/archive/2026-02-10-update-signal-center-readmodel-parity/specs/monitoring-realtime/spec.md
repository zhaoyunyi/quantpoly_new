## ADDED Requirements

### Requirement: 监控摘要与信号中心统计口径必须一致
监控摘要中的信号统计 MUST 与信号中心仪表板保持同一字段定义。

#### Scenario: 摘要与仪表板信号计数一致
- **GIVEN** 用户拥有已知数量的 pending/expired 信号
- **WHEN** 分别读取监控摘要与信号仪表板
- **THEN** 两者信号计数字段语义一致
- **AND** 数据范围均仅限当前用户
