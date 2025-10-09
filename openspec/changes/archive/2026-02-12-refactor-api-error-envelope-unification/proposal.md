## Why

当前 API 的错误响应在“组合入口（backend_app）”与“standalone app/测试 app”之间不一致：

- 组合入口会把 `HTTPException/ValidationError` 统一封装为 `error_response`。
- 但部分 standalone app/测试 app 仍返回 FastAPI 默认 `{"detail": ...}`。

这会导致同一能力在不同运行形态下契约漂移，且 `user-auth` 的业务错误码（如 `EMAIL_NOT_VERIFIED`）在部分链路下会丢失，违背 spec 中“可识别业务错误码”的要求。

## What Changes

- 在 `platform-core` 增加 FastAPI 异常处理安装器（如 `install_exception_handlers(app)`），统一 `HTTPException / RequestValidationError / Exception` → `error_response`。
- `backend_app` 与 `user-auth` standalone app、典型测试 harness 显式安装该处理器。
- `user-auth` 关键业务错误统一使用结构化 `detail={code,message}`，确保 `error.code` 保真。
- 更新相关测试断言：从 `detail` 改为 `error.code/error.message`。

## Impact

- 影响 capability：`platform-core`、`user-auth`、`backend-app`
- **BREAKING**：standalone 形态下的错误响应体从 FastAPI 默认 `detail` 变为 `error_response` envelope（HTTP status code 保持不变）。

