## ADDED Requirements

### Requirement: 当前用户资料读写必须统一使用 /users/me

系统 MUST 提供单一路由语义来表示“当前用户资源（me）”，并将读取与写入统一收敛在 `/users/me` 路径下，避免 `/auth` 与 `/users` 同时承载同一资源语义。

#### Scenario: 读取当前用户使用 GET /users/me

- **GIVEN** 用户已认证
- **WHEN** 调用 `GET /users/me`
- **THEN** 返回当前用户资料

#### Scenario: 更新当前用户使用 PATCH /users/me

- **GIVEN** 用户已认证
- **WHEN** 调用 `PATCH /users/me`
- **THEN** 返回更新后的用户资料

