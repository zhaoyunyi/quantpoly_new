## 1. 密码找回领域模型

- [x] 1.1 定义 PasswordResetToken 聚合（issued/consumed/expired）
- [x] 1.2 定义 token 持久化仓储接口与 sqlite 适配器
- [x] 1.3 明确 token 单次消费与过期策略

## 2. API 与安全语义

- [x] 2.1 调整 `/auth/password-reset/request` 响应，不返回明文 token
- [x] 2.2 补齐抗枚举语义（用户不存在也返回统一响应）
- [x] 2.3 增加频控与审计字段（最小可观测）

## 3. CLI 与运维可测试性

- [x] 3.1 增加受控测试模式（仅测试环境可读取 reset token）
- [x] 3.2 CLI 增加 password-reset request/confirm 子命令对齐
- [x] 3.3 更新迁移说明（break update）

## 4. 测试与验证

- [x] 4.1 先写失败测试（Red）：重启恢复、重复消费、过期拒绝
- [x] 4.2 补齐 API/CLI 回归测试（含频控与枚举保护）
- [x] 4.3 运行 `openspec validate update-user-auth-password-recovery-hardening --strict`
