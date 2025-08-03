## ADDED Requirements

### Requirement: 偏好接口契约必须版本化且稳定
`user-preferences` MUST 提供稳定的响应 envelope 与版本字段，保证迁移期前后端可兼容。

#### Scenario: 读取偏好返回标准 envelope
- **GIVEN** 用户调用 `GET /users/me/preferences`
- **WHEN** 后端返回数据
- **THEN** 响应包含 `success`、`message`、`data`
- **AND** `data.version` 字段存在且可用于迁移判断

### Requirement: 偏好写入冲突由服务端裁决
偏好更新冲突 MUST 在服务端按照明确策略处理，避免前端本地兜底造成数据分叉。

#### Scenario: 并发更新时服务端给出一致结果
- **GIVEN** 同一用户在两个客户端并发更新偏好
- **WHEN** 请求到达后端
- **THEN** 后端按统一 merge 规则生成最终偏好
- **AND** 返回结果可被后续客户端直接复用

