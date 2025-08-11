## ADDED Requirements

### Requirement: 行情服务必须支持目录与批量查询
市场数据服务 MUST 提供标的目录、符号清单、批量报价与最新行情查询能力。

#### Scenario: 用户批量查询多个标的报价
- **GIVEN** 用户提交多个股票代码
- **WHEN** 调用批量报价接口
- **THEN** 返回每个标的的最新报价或明确错误状态
- **AND** 响应包含统一时间戳与来源标记

### Requirement: 行情上游异常必须有统一降级语义
当上游 Provider 超时或限流时，服务 MUST 返回可识别错误码并支持重试判断。

#### Scenario: 上游限流时返回稳定错误码
- **GIVEN** 上游 provider 触发 rate limit
- **WHEN** 用户调用行情接口
- **THEN** 返回标准错误 envelope
- **AND** 错误码标识为可重试或需退避
