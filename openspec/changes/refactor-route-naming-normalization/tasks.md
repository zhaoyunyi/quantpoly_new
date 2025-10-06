## 1. user-auth 路由语义统一

- [ ] 1.1 Red：`GET /users/me` 返回当前用户资料
- [ ] 1.2 Green：实现/迁移 `GET /auth/me` → `GET /users/me`
- [ ] 1.3 Green：移除或拒绝 `/auth/me`（按 break update 策略）

## 2. 回归与规范校验

- [ ] 2.1 运行 `.venv/bin/pytest -q`
- [ ] 2.2 运行 `openspec validate refactor-route-naming-normalization --strict`

