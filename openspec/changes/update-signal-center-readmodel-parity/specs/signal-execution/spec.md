## ADDED Requirements

### Requirement: 信号生命周期必须支持详情与过期状态迁移
信号系统 MUST 提供信号详情读取与过期状态迁移能力。

#### Scenario: 信号过期迁移后不可执行
- **GIVEN** 信号已超过过期时间
- **WHEN** 系统执行过期迁移
- **THEN** 信号状态变为 `expired`
- **AND** 后续执行请求被拒绝

### Requirement: 信号中心必须提供筛选搜索与账户仪表板
信号系统 MUST 提供 pending/expired 筛选、搜索与账户维度统计仪表板。

#### Scenario: 查询账户信号仪表板
- **GIVEN** 账户存在多个状态的信号
- **WHEN** 调用仪表板接口
- **THEN** 返回按状态聚合的信号统计
- **AND** 不包含其他用户账户数据
