## ADDED Requirements

### Requirement: 密码找回 token 必须持久化并单次消费
密码找回流程 MUST 使用持久化 token 存储，并保证 token 只能被消费一次且支持过期控制。

#### Scenario: 服务重启后找回 token 仍可验证
- **GIVEN** 用户已发起密码找回并收到有效 token
- **WHEN** 后端服务重启
- **THEN** token 仍可用于重置密码
- **AND** 重置成功后该 token 立即失效

#### Scenario: 重复使用同一 token 被拒绝
- **GIVEN** token 已被成功消费一次
- **WHEN** 用户再次提交同一 token
- **THEN** 返回安全错误响应
- **AND** 不允许重复重置密码

### Requirement: 密码找回请求不得返回明文 token
`/auth/password-reset/request` MUST 返回统一受控响应，不得直接泄漏明文 reset token。

#### Scenario: 请求密码找回返回统一成功语义
- **GIVEN** 用户提交邮箱发起找回
- **WHEN** 系统受理请求
- **THEN** 返回统一成功响应
- **AND** 响应中不包含 reset token 明文字段

#### Scenario: 不存在邮箱也返回抗枚举响应
- **GIVEN** 请求邮箱不存在
- **WHEN** 调用密码找回请求接口
- **THEN** 返回与存在邮箱一致的成功语义
- **AND** 系统记录审计事件用于安全追踪
