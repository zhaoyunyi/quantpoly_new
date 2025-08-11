## 1. 领域与仓储扩展

- [x] 1.1 扩展用户聚合：状态（active/disabled）与等级（level）变更规则
- [x] 1.2 扩展用户仓储：分页查询、按状态筛选、等级更新
- [x] 1.3 扩展会话仓储：按用户批量失效会话

## 2. API 与 CLI 能力补齐

- [x] 2.1 新增 `PATCH /users/me`（资料更新）
- [x] 2.2 新增 `PATCH /users/me/password`（密码修改 + 会话失效）
- [x] 2.3 新增 `GET /admin/users`、`PATCH /admin/users/{id}`（管理员治理）
- [x] 2.4 提供对应 CLI 命令并保证 JSON 输出

## 3. 治理与审计

- [x] 3.1 将用户管理动作接入 `admin-governance` 动作目录
- [x] 3.2 审计日志记录 `actor/action/target/result/timestamp`
- [x] 3.3 敏感字段脱敏（token/cookie/password）

## 4. 测试与校验

- [x] 4.1 按 TDD 增加领域/API/CLI 测试（Given/When/Then）
- [x] 4.2 验证普通用户访问管理员接口返回 403
- [x] 4.3 运行 `openspec validate update-user-account-governance-parity --strict`
