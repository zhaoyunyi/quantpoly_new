# frontend-settings Specification

## Purpose
TBD - created by archiving change add-frontend-settings-pages. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL provide settings pages backed by user-preferences and user-auth

前端 SHALL 提供 `/settings`、`/settings/theme`、`/settings/account`，并通过后端接口持久化偏好与账户资料变更。

#### Scenario: Patch preferences persists to backend
- **GIVEN** 用户已登录
- **WHEN** 用户在 `/settings` 修改偏好并保存
- **THEN** 前端调用 `PATCH /users/me/preferences`
- **AND** 刷新后偏好仍保持一致

