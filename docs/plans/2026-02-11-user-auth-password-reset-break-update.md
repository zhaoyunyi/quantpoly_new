# user-auth 密码找回加固迁移说明（break update）

## 背景

`user-auth` 在密码找回流程中完成了安全加固：

- 重置 token 从内存态升级为持久化存储（SQLite）
- token 采用摘要存储（SHA-256），并强制单次消费
- `password-reset/request` 默认不再返回明文 token
- 新增最小频控与审计事件输出

这是一项 **break update**：旧有依赖“接口直出 reset token”的调用方式将失效。

## 变更清单

## 1. API 语义变更

### 1.1 `POST /auth/password-reset/request`

- **旧行为**：可能返回 `data.resetToken`
- **新行为**：统一返回成功语义，不返回 token 明文
- **抗枚举语义**：邮箱存在与否，响应结构与 message 保持一致

### 1.2 受控测试模式

当 `create_app(password_reset_test_mode=True)` 时，允许在测试环境返回 `data.resetToken`。

> 仅用于测试，不应在生产环境开启。

### 1.3 `POST /auth/password-reset/confirm`

- token 无效、过期、重复消费：返回失败
- 密码更新后会撤销该用户现有会话

## 2. CLI 变更

新增命令：

- `password-reset-request --email <email>`
- `password-reset-confirm --token <token> --new-password <password>`

CLI 输出保持 JSON，便于脚本化集成。

## 3. 对调用方影响

## 3.1 前端/脚本调用

若此前直接读取 `request` 响应中的 `resetToken`，需改为：

- 生产：改为邮件/消息通道投递 token（后续接入）
- 测试：启用 `password_reset_test_mode=True` 获取 token

## 3.2 自动化测试

- 集成测试应改为测试模式下获取 token
- 增加用例覆盖：单次消费、过期拒绝、抗枚举响应一致

## 迁移步骤

1. 升级后端到本次变更版本。
2. 检查所有 `password-reset/request` 调用点，移除对 `data.resetToken` 的生产依赖。
3. 将测试环境应用实例改为 `password_reset_test_mode=True`（仅测试进程）。
4. 回归验证：
   - 重置后旧密码不可登录
   - 同一 token 不能二次使用
   - 不存在邮箱与存在邮箱请求响应一致

## 回滚策略

- 若需紧急回滚，可回退至变更前版本。
- 回滚后应注意：
  - 内存 token 方案不支持进程重启恢复
  - 响应中可能再次泄漏 token 明文
- 建议仅作为临时兜底，尽快恢复加固版本。
