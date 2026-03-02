## 1. 路由与页面

- [ ] 1.1 新增 `/auth/login`：邮箱/密码表单，支持 `next` 重定向
- [ ] 1.2 新增 `/auth/register`：注册表单（最小字段：email/password）
- [ ] 1.3 新增 `/auth/forgot-password`：发起找回（调用 `POST /auth/password-reset/request`）
- [ ] 1.4 新增 `/auth/reset-password`：从 query 读取 token，提交新密码（调用 `POST /auth/password-reset/confirm`）
- [ ] 1.5 新增 `/auth/verify-email`：按后端当前契约实现（输入 email 或从 query 读取 email），调用 `POST /auth/verify-email`
- [ ] 1.6 新增 `/auth/resend-verification`：
  - [ ] 若后端提供 resend 端点则直连调用
  - [ ] 否则以“提示 + 引导验证/找回”作为临时降级（并在任务中明确后端缺口）

## 2. API 对接（frontend_api_client）

- [ ] 2.1 增加 endpoints：
  - [ ] `auth.register`
  - [ ] `auth.login`（必须 `credentials: include`）
  - [ ] `auth.logout`
  - [ ] `auth.verify_email`
  - [ ] `auth.password_reset_request`
  - [ ] `auth.password_reset_confirm`
  - [ ] `users.me.get`
- [ ] 2.2 统一错误码展示：
  - [ ] `EMAIL_NOT_VERIFIED`：提示去 `/auth/verify-email` 或 `/auth/resend-verification`
  - [ ] `USER_DISABLED`：提示联系管理员

## 3. 交互与可访问性

- [ ] 3.1 表单字段校验：email 格式、密码强度提示（不泄漏过多策略细节）
- [ ] 3.2 键盘可达与焦点环（符合 `spec/UISpec.md`）

## 4. 测试（TDD）

- [ ] 4.1 单元测试：登录页在 401 时展示错误信息；在成功时跳转 `next`
- [ ] 4.2 单元测试：找回/重置流程的成功与失败分支

## 5. 回归验证

- [ ] 5.1 `cd apps/frontend_web && npm run build`
- [ ] 5.2 `pytest -q`

