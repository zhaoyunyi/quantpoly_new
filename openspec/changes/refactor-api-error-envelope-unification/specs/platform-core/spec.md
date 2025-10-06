## ADDED Requirements

### Requirement: 平台核心库必须提供 FastAPI 异常信封安装器

平台核心库 MUST 提供可复用的 FastAPI 异常处理安装器，用于将常见异常统一映射为 `error_response` 信封，以确保不同 bounded context 与不同组合形态（standalone/组合入口/测试 app）下的错误响应结构一致。

#### Scenario: HTTPException 映射为 error_response

- **GIVEN** 一个安装了平台异常处理安装器的 FastAPI app
- **WHEN** 路由抛出 `HTTPException(status_code=403, detail={code:"EMAIL_NOT_VERIFIED", message:"email not verified"})`
- **THEN** 响应体为 `success=false`
- **AND** `error.code` 等于 `EMAIL_NOT_VERIFIED`

#### Scenario: RequestValidationError 映射为 VALIDATION_ERROR

- **GIVEN** 一个安装了平台异常处理安装器的 FastAPI app
- **WHEN** 请求体校验失败触发 `RequestValidationError`
- **THEN** 返回 422
- **AND** 响应 `error.code` 等于 `VALIDATION_ERROR`

