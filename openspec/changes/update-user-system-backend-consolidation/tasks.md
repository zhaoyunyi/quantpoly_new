## 1. 领域与存储

- [x] 1.1 为 `user_auth` 增加持久化仓储与会话存储抽象（保留 in-memory 作为测试实现）
- [x] 1.2 增加用户表/会话表迁移脚本与兼容读取策略
- [x] 1.3 建立 legacy better-auth token/cookie 兼容解析器并补充单元测试

## 2. 认证流程

- [x] 2.1 实现邮箱验证流程（注册后验证、未验证登录限制）
- [x] 2.2 实现密码找回/重置流程（token 生成、过期、单次使用）
- [x] 2.3 统一 `get_current_user` 在 HTTP/WebSocket/CLI 的行为与错误码

## 3. 偏好契约对齐

- [x] 3.1 扩展 `user_preferences` 领域模型，支持版本化迁移策略
- [x] 3.2 统一偏好 API 响应 envelope 与字段命名规范（camelCase 对外）
- [x] 3.3 明确并实现服务端 merge 语义，移除前端本地兜底依赖

## 4. 安全与验证

- [x] 4.1 在 `platform_core` 脱敏规则中补充 token/cookie 请求上下文脱敏
- [x] 4.2 增加鉴权失败日志审计测试，确保无明文 token/body 泄漏
- [x] 4.3 运行 `pytest -q` 与 `openspec validate update-user-system-backend-consolidation --strict`
