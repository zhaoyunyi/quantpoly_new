## 1. `/settings` 偏好总览

- [x] 1.1 拉取偏好：`GET /users/me/preferences`
- [x] 1.2 支持 patch 更新：`PATCH /users/me/preferences`（仅更新相关子树）
- [x] 1.3 支持 reset：`POST /users/me/preferences/reset`
- [x] 1.4 支持导入/导出：
  - [x] `GET /users/me/preferences/export`
  - [x] `POST /users/me/preferences/import`

## 2. `/settings/theme` 主题偏好

- [x] 2.1 主题模式（light/dark/auto）写入 preferences.theme（按后端 schema）
- [x] 2.2 主色/密度/动画开关（如有需求）写入 preferences
- [x] 2.3 前端应用侧：读取 preferences 并映射到 tokens（仅通过 tokens 层，不直接写组件色值）

## 3. `/settings/account` 账户资料与安全

- [x] 3.1 资料读取：`GET /users/me`
- [x] 3.2 资料更新：`PATCH /users/me`（email/displayName）
- [x] 3.3 改密：`PATCH /users/me/password`
- [x] 3.4 注销：`DELETE /users/me`（危险操作二次确认）

## 4. 组件规划

- [x] 4.1 `PreferencesForm`（JSON patch 语义）
- [x] 4.2 `ThemePreferencesForm`
- [x] 4.3 `AccountProfileForm`
- [x] 4.4 `DangerZone`（改密/注销）

## 5. 测试（TDD）

- [x] 5.1 单元测试：preferences patch 后刷新展示
- [x] 5.2 单元测试：注销确认对话框的禁用/确认逻辑

## 6. 回归验证

- [x] 6.1 `cd apps/frontend_web && npm run build`
- [x] 6.2 `pytest -q`
