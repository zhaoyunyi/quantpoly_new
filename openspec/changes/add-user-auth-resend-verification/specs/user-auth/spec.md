## ADDED Requirements

### Requirement: 后端 MUST 提供重发邮箱验证流程端点

后端 MUST 提供“重发邮箱验证”端点，用于在登录返回 `EMAIL_NOT_VERIFIED` 时触发重新发送验证邮件流程。

#### Scenario: Resend endpoint returns anti-enumeration success
- **GIVEN** 用户提交邮箱请求重发验证
- **WHEN** 调用 `POST /auth/verify-email/resend`
- **THEN** 总是返回统一成功语义
- **AND** 不泄漏邮箱是否存在或是否已验证

