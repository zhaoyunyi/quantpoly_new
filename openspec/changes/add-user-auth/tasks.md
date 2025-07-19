# add-user-auth Tasks

## 1. 规范与设计

- [ ] 1.1 创建 capability `user-auth` 的 spec（`openspec/specs/user-auth/spec.md`）
- [ ] 1.2 创建 `user-auth` 设计说明（`openspec/specs/user-auth/design.md`）

## 2. 代码落地（后续执行阶段）

> 说明：实现阶段遵循 `spec/ProgramSpec.md` 严格 TDD。

- [ ] 2.1 建立 `user_auth` library：用户、凭证、会话、权限
- [ ] 2.2 提供 CLI：`user-auth`（创建用户/登录/验证 token/登出）
- [ ] 2.3 提供 FastAPI 依赖：`get_current_user`（单一来源、可配置协议）
- [ ] 2.4 添加单元测试与集成测试（包含安全边界：token 泄漏、弱口令、会话撤销）

