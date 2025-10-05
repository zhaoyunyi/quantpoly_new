## ADDED Requirements

### Requirement: 信号全局维护接口不得接受 legacy is_admin
信号系统全局维护接口 MUST 不再接受 `is_admin` 字段作为管理员权限来源。

#### Scenario: legacy is_admin 调用全局维护被拒绝
- **GIVEN** 当前用户仅包含 `is_admin=true` 且无 `role=admin`
- **WHEN** 调用全局维护/清理接口
- **THEN** 返回 403
- **AND** 错误码为 `ADMIN_REQUIRED`
