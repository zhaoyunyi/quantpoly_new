# frontend-testing-harness Specification

## Purpose
TBD - created by archiving change add-frontend-testing-harness. Update Purpose after archive.
## Requirements
### Requirement: Frontend MUST provide automated tests for critical user journeys

前端 MUST 提供自动化测试覆盖关键用户旅程，并在重构过程中作为回归门禁。

#### Scenario: E2E covers login and dashboard entry
- **GIVEN** 后端服务可用且存在可登录用户
- **WHEN** 运行 E2E 用例
- **THEN** 自动化流程完成登录并进入 `/dashboard`

