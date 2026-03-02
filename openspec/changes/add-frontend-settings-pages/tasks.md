## 1. `/settings` 偏好总览

- [ ] 1.1 拉取偏好：`GET /users/me/preferences`
- [ ] 1.2 支持 patch 更新：`PATCH /users/me/preferences`（仅更新相关子树）
- [ ] 1.3 支持 reset：`POST /users/me/preferences/reset`
- [ ] 1.4 支持导入/导出：
  - [ ] `GET /users/me/preferences/export`
  - [ ] `POST /users/me/preferences/import`

## 2. `/settings/theme` 主题偏好

- [ ] 2.1 主题模式（light/dark/auto）写入 preferences.theme（按后端 schema）
- [ ] 2.2 主色/密度/动画开关（如有需求）写入 preferences
- [ ] 2.3 前端应用侧：读取 preferences 并映射到 tokens（仅通过 tokens 层，不直接写组件色值）

## 3. `/settings/account` 账户资料与安全

- [ ] 3.1 资料读取：`GET /users/me`
- [ ] 3.2 资料更新：`PATCH /users/me`（email/displayName）
- [ ] 3.3 改密：`PATCH /users/me/password`
- [ ] 3.4 注销：`DELETE /users/me`（危险操作二次确认）

## 4. 组件规划

- [ ] 4.1 `PreferencesForm`（JSON patch 语义）
- [ ] 4.2 `ThemePreferencesForm`
- [ ] 4.3 `AccountProfileForm`
- [ ] 4.4 `DangerZone`（改密/注销）

## 5. 测试（TDD）

- [ ] 5.1 单元测试：preferences patch 后刷新展示
- [ ] 5.2 单元测试：注销确认对话框的禁用/确认逻辑

## 6. 回归验证

- [ ] 6.1 `cd apps/frontend_web && npm run build`
- [ ] 6.2 `pytest -q`

