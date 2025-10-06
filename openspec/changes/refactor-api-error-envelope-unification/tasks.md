## 1. platform-core：异常信封安装器

- [ ] 1.1 Red：安装处理器后，`HTTPException` 返回 `error_response`
- [ ] 1.2 Red：安装处理器后，`RequestValidationError` 返回 `VALIDATION_ERROR`
- [ ] 1.3 Red：安装处理器后，未知异常返回 `INTERNAL_ERROR`
- [ ] 1.4 Green：实现 `install_exception_handlers(app)` 并在最小样例中验证

## 2. backend-app：复用平台安装器

- [ ] 2.1 将 backend_app 的通用异常处理改为复用平台安装器（保留 `PermissionError` 映射差异点）

## 3. user-auth：业务错误码保真

- [ ] 3.1 Red：未验证邮箱登录返回 `error.code=EMAIL_NOT_VERIFIED`
- [ ] 3.2 Red：禁用用户登录返回 `error.code=USER_DISABLED`
- [ ] 3.3 Red：缺 token 访问受保护接口返回 `error.code=MISSING_TOKEN`
- [ ] 3.4 Green：调整 `HTTPException.detail` 为 `{code,message}`，并安装异常处理器

## 4. 回归与规范校验

- [ ] 4.1 运行 `.venv/bin/pytest -q`
- [ ] 4.2 运行 `openspec validate refactor-api-error-envelope-unification --strict`

