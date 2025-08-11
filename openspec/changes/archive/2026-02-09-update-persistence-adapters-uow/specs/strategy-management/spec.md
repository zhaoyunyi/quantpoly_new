## ADDED Requirements

### Requirement: 策略状态变更必须持久化并在重启后可恢复
策略创建、更新、删除保护与状态变更 MUST 进入持久化路径，不得依赖 in-memory 主状态。

#### Scenario: 服务重启后策略状态可恢复
- **GIVEN** 用户已创建并更新策略状态
- **WHEN** 服务发生重启
- **THEN** 重新读取策略时必须返回重启前已提交状态
- **AND** 删除保护规则仍然生效
