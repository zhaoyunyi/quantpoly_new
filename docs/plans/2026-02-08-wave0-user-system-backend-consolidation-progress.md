# Wave 0 用户系统后端聚合 - 进度记录（第一阶段）

## 本阶段已完成

- `legacy token` 兼容（`token.signature` + better-auth cookies）
  - `Authorization: Bearer token.signature`
  - `__Secure-better-auth.session_token`
  - `better-auth.session_token`
- `user_auth` 持久化基座接入
  - `SQLiteUserRepository`
  - `SQLiteSessionStore`
  - `create_app(sqlite_db_path=...)`
- 邮箱验证流程
  - 注册默认 `email_verified=False`
  - `POST /auth/verify-email`
  - 未验证邮箱登录返回 `403 EMAIL_NOT_VERIFIED`
- 密码找回/重置流程
  - `POST /auth/password-reset/request`
  - `POST /auth/password-reset/confirm`
  - reset token 单次使用
- 统一鉴权错误码语义（2.3）
  - HTTP `get_current_user` 返回结构化 detail：
    - `MISSING_TOKEN`
    - `INVALID_TOKEN`
    - `USER_NOT_FOUND`
  - WebSocket 统一未认证关闭码：`4401`
  - CLI 统一错误码：`INVALID_TOKEN` 等
- 日志脱敏增强
  - `platform_core.logging` 支持 JSON-like 场景敏感字段掩码
  - 鉴权失败日志测试覆盖无明文 token 泄漏
- `user_preferences` 契约对齐
  - 扩展默认契约：`theme/account/notifications/data/advanced/lastUpdated/syncEnabled`
  - `migrate_preferences` 支持 legacy partial payload（Mapping 输入）
  - `PATCH /users/me/preferences` 服务端深度 merge + `lastUpdated` 由服务端裁决
  - `import` 支持旧版本 payload 自动迁移

## 关键文件

- `libs/user_auth/user_auth/token.py`
- `libs/user_auth/user_auth/session_sqlite.py`
- `libs/user_auth/user_auth/repository_sqlite.py`
- `libs/user_auth/user_auth/app.py`
- `libs/user_auth/user_auth/password_reset.py`
- `libs/user_auth/user_auth/cli.py`
- `libs/platform_core/platform_core/logging.py`
- `libs/user_preferences/user_preferences/domain.py`
- `libs/user_preferences/user_preferences/api.py`
- `libs/user_preferences/user_preferences/cli.py`
- `openspec/changes/update-user-system-backend-consolidation/tasks.md`

## 验证结果

- `pytest -q`：通过（127 passed）
- `openspec validate update-user-system-backend-consolidation --strict`：通过
- `openspec validate --changes --strict`：通过（9/9）

## 下一阶段建议（继续“统一推进”）

1. 收敛前端用户职责：仅保留 UI + API 调用（移除本地鉴权兜底逻辑）
2. 准备进入 Wave 1：`strategy/backtest` 与 `trading-account` 并行迁移
3. 为 Wave 1 建立最小 ACL 接口，避免跨上下文直接依赖
