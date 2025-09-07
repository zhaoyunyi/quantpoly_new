## ADDED Requirements

### Requirement: 交易系统必须支持可控的订单更新与删除
交易系统 MUST 支持对可编辑状态订单执行更新与删除（撤销）操作，并保持状态机约束。

#### Scenario: 更新 pending 订单成功
- **GIVEN** 用户拥有一个 `pending/open` 订单
- **WHEN** 调用订单更新接口修改可编辑字段
- **THEN** 返回更新后的订单
- **AND** 订单状态仍满足状态机约束

#### Scenario: 删除订单等价于受控撤销
- **GIVEN** 用户拥有一个可撤销订单
- **WHEN** 调用订单删除接口
- **THEN** 订单状态迁移为 `cancelled`
- **AND** 返回可追踪的撤销结果

### Requirement: 交易系统必须提供仓位与待处理交易快捷查询
交易系统 MUST 提供按标的单仓位查询与账户待处理交易查询能力，支撑交易运营与排障。

#### Scenario: 按标的查询单仓位
- **GIVEN** 账户持有某个标的仓位
- **WHEN** 调用单仓位查询接口
- **THEN** 返回该标的仓位详情

#### Scenario: 查询账户待处理交易
- **GIVEN** 账户存在 `pending/open` 交易
- **WHEN** 调用待处理交易查询接口
- **THEN** 返回仅包含待处理状态的交易记录
