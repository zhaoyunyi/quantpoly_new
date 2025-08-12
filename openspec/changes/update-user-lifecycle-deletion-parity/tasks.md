## 1. 领域与仓储扩展

- [ ] 1.1 增加用户自助注销的领域规则（状态迁移与不可逆约束）
- [ ] 1.2 扩展仓储删除能力（软删除/硬删除策略落地）
- [ ] 1.3 删除后批量失效会话与重置凭证索引

## 2. API 与 CLI 补齐

- [ ] 2.1 新增 `DELETE /users/me`（自助注销）
- [ ] 2.2 新增 `GET /admin/users/{id}`（管理员详情）
- [ ] 2.3 新增 `DELETE /admin/users/{id}`（管理员删除）
- [ ] 2.4 提供对应 CLI 子命令与 JSON 输出

## 3. 治理与审计

- [ ] 3.1 用户删除动作接入 `admin-governance` 授权
- [ ] 3.2 审计日志记录 `actor/action/target/result/timestamp`
- [ ] 3.3 删除链路日志敏感字段全量脱敏

## 4. 测试与校验

- [ ] 4.1 按 TDD 增加领域/仓储/API/CLI 测试
- [ ] 4.2 覆盖普通用户越权删除管理员目标用例
- [ ] 4.3 运行 `openspec validate update-user-lifecycle-deletion-parity --strict`
