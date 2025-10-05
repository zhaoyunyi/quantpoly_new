## ADDED Requirements

### Requirement: 管理员判定必须基于 role/level
平台核心鉴权辅助 MUST 基于 `role/level` 判定管理员身份，不得接受 legacy `is_admin` 字段作为权限来源。

#### Scenario: legacy is_admin 字段不再触发管理员权限
- **GIVEN** actor 仅包含 `is_admin=true` 且无 `role=admin`
- **WHEN** 组合入口判定管理员权限
- **THEN** 判定结果为非管理员
- **AND** 返回稳定判权来源（如 `none`）
