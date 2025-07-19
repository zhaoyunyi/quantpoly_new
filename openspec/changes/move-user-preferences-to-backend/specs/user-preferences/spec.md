## ADDED Requirements

### Requirement: 后端持有偏好设置的默认值与版本
后端 MUST 维护用户偏好设置的默认值与 `version`，并能对旧版本偏好进行迁移。

#### Scenario: 新用户首次读取偏好得到默认值
- **GIVEN** 用户首次调用 `GET /users/me/preferences`
- **WHEN** 用户尚无 preferences
- **THEN** 返回默认 preferences
- **AND** 在持久化层保存该默认值（避免重复生成）

#### Scenario: 旧版本 preferences 自动迁移
- **GIVEN** 用户 preferences `version` 低于当前版本
- **WHEN** 用户读取偏好
- **THEN** 后端执行迁移并返回新版本结构

### Requirement: 偏好更新支持深度合并与字段校验
后端 MUST 支持对偏好设置进行部分更新，并对更新字段做校验。

#### Scenario: 深度合并不丢失未更新字段
- **GIVEN** 用户已有 preferences（含嵌套对象）
- **WHEN** 用户 PATCH 仅更新 `theme.primaryColor`
- **THEN** `theme` 的其他字段保持不变

#### Scenario: 非法字段被拒绝
- **GIVEN** 用户 PATCH 包含不支持字段
- **WHEN** 后端校验请求体
- **THEN** 返回 400/422 并提示不支持字段

### Requirement: advanced 字段具备等级权限
偏好设置中的 `advanced` 字段 MUST 受用户等级或角色控制。

#### Scenario: 低等级用户看不到 advanced
- **GIVEN** 用户等级为 Level 1
- **WHEN** 调用 `GET /users/me/preferences`
- **THEN** 响应中不包含 `advanced`

#### Scenario: 低等级用户不能写 advanced
- **GIVEN** 用户等级为 Level 1
- **WHEN** PATCH 包含 `advanced`
- **THEN** 返回 403

### Requirement: 偏好支持 reset/export/import
后端 MUST 提供偏好重置、导出、导入接口，以支持跨端同步与备份。

#### Scenario: reset 恢复默认值
- **GIVEN** 用户已修改偏好
- **WHEN** 调用 reset
- **THEN** 偏好恢复默认值并返回新偏好

#### Scenario: export 返回可导入的 JSON
- **GIVEN** 用户请求导出
- **WHEN** 调用 export
- **THEN** 返回 JSON（含 version）

#### Scenario: import 校验并写入
- **GIVEN** 用户提交导入 JSON
- **WHEN** JSON 通过校验
- **THEN** 写入并返回更新后的 preferences

