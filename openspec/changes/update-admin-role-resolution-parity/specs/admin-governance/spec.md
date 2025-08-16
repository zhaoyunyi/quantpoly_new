## ADDED Requirements

### Requirement: 治理层必须统一解释管理员身份来源
治理系统 MUST 统一解释管理员身份来源（`role/level/is_admin`），并记录最终判定依据。

#### Scenario: 管理员身份来源可追踪
- **GIVEN** 系统接收到高风险管理员动作
- **WHEN** 治理层完成鉴权与执行
- **THEN** 审计记录包含 `role/level/is_admin` 的判定摘要
- **AND** 敏感字段保持脱敏
