## ADDED Requirements

### Requirement: 策略必须支持模板化创建与受控状态迁移
策略管理 MUST 提供模板能力，并由领域状态机约束策略生命周期迁移。

#### Scenario: 从模板创建策略并成功激活
- **GIVEN** 用户选择一个可用策略模板
- **WHEN** 提交参数并创建策略后执行激活
- **THEN** 策略状态从 `draft` 迁移到 `active`
- **AND** 迁移过程记录参数校验结果

#### Scenario: 非法状态迁移被拒绝
- **GIVEN** 策略处于 `archived` 状态
- **WHEN** 用户尝试直接激活策略
- **THEN** 后端返回 409
- **AND** 错误码可用于前端识别状态冲突
