## 1. 需求与合同（Spec）

- [ ] 1.1 增加管理员创建用户需求 delta
- [ ] 1.2 增加管理员创建用户审计需求 delta
- [ ] 1.3 增加 API/CLI 合同测试（管理员/非管理员）

## 2. Library-First 实现

- [ ] 2.1 扩展 `UserRepository` 与 `UserAuthService`（管理员创建用户）
- [ ] 2.2 在治理层接入 `admin_create_user` 审计事件
- [ ] 2.3 扩展 CLI 命令（admin-create-user）

## 3. API

- [ ] 3.1 增加 `POST /admin/users`（管理员创建用户）
- [ ] 3.2 统一错误码与响应 envelope

## 4. 验证

- [ ] 4.1 运行 `pytest -q libs/user_auth/tests libs/admin_governance/tests`
- [ ] 4.2 运行 `openspec validate update-user-admin-provisioning-parity --type change --strict`
