## ADDED Requirements

### Requirement: 风险评估必须支持账户快照查询与主动评估
风控系统 MUST 提供账户风险快照读取与主动 evaluate 触发能力。

#### Scenario: 主动触发账户风险评估
- **GIVEN** 用户账户存在持仓与交易数据
- **WHEN** 调用风险评估 evaluate 接口
- **THEN** 返回最新风险快照
- **AND** 快照包含风险分值、等级与建议
