## ADDED Requirements

### Requirement: 偏好存储必须遵循组合入口持久化配置
用户偏好上下文 MUST 在 `storage_backend=sqlite` 场景下使用可持久化存储，以保证偏好在重启后不丢失。

#### Scenario: sqlite 模式重启后偏好保持不变
- **GIVEN** 用户已更新偏好设置并写入存储
- **WHEN** 服务重启后再次读取偏好
- **THEN** 返回重启前最后一次写入结果
- **AND** 版本字段与结构保持有效
