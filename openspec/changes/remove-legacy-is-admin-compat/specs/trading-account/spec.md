## ADDED Requirements

### Requirement: 交易运维接口不得接受 legacy is_admin
交易运维接口 MUST 不再接受 `is_admin` 字段作为管理员权限来源。

#### Scenario: legacy is_admin 访问运维接口被拒绝
- **GIVEN** 当前用户仅包含 `is_admin=true` 且无 `role=admin`
- **WHEN** 调用 trading ops 接口（如刷新价格/待处理订单）
- **THEN** 返回 403
- **AND** 错误码为 `ADMIN_REQUIRED`
