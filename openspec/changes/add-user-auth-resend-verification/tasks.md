## 1. API 设计与实现（TDD）

- [ ] 1.1 新增失败测试：存在用户/不存在用户均返回统一 success 语义
- [ ] 1.2 新增失败测试：已验证用户也返回统一 success（避免枚举）
- [ ] 1.3 实现端点：`POST /auth/verify-email/resend`
- [ ] 1.4 记录审计日志（不记录敏感信息）

## 2. 文档与回归

- [ ] 2.1 更新 `user-auth` spec delta
- [ ] 2.2 `pytest -q`

