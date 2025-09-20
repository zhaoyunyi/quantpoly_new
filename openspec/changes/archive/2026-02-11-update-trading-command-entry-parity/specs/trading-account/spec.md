## ADDED Requirements

### Requirement: 交易系统必须提供业务级买卖指令入口
交易系统 MUST 提供 buy/sell 业务指令入口，以支持“下单即表达交易意图”的产品流程；内部实现 MAY 复用订单聚合与状态机。

#### Scenario: buy 指令成功生成交易结果
- **GIVEN** 用户账户资金充足且风控允许
- **WHEN** 用户提交 buy 指令
- **THEN** 系统生成可追踪订单与成交结果
- **AND** 账户资金与持仓按事务一致性更新

#### Scenario: buy 指令资金不足被拒绝
- **GIVEN** 用户账户可用资金不足
- **WHEN** 用户提交 buy 指令
- **THEN** 返回可识别错误码（如资金不足）
- **AND** 不得写入部分成交或异常流水
