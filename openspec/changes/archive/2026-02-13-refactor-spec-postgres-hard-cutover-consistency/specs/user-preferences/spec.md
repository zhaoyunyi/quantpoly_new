## RENAMED Requirements

- FROM: `### Requirement: 偏好存储必须提供 sqlite 持久化适配器`
- TO: `### Requirement: 偏好存储必须提供 postgres 持久化适配器`

## MODIFIED Requirements

### Requirement: 偏好存储必须提供 postgres 持久化适配器
偏好上下文 MUST 提供 postgres 持久化适配器，并在 postgres 运行模式下保存用户偏好变更。

#### Scenario: 偏好更新后重启仍可读取
- **GIVEN** 用户已成功更新偏好
- **WHEN** 服务重启并再次读取偏好
- **THEN** 返回重启前最后一次保存值
- **AND** `version` 字段保持有效
