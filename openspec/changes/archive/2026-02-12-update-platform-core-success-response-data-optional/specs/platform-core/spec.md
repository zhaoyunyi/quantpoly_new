## MODIFIED Requirements

### Requirement: 平台核心库提供统一的 API 响应信封

平台核心库 MUST 提供统一的 API 响应信封（success/error/paged），并能在 FastAPI 路由中直接复用。

#### Scenario: success_response 返回带 data 的一致结构

- **GIVEN** 任意业务接口执行成功且需要返回业务数据
- **WHEN** 返回 `success_response(data, message)`
- **THEN** 响应体包含 `success=true`、`message`、`data`

#### Scenario: success_response 在无 data 时省略 data 字段

- **GIVEN** 任意业务接口执行成功但不需要返回业务数据
- **WHEN** 返回 `success_response(message=...)`（或 `success_response()`）
- **THEN** 响应体包含 `success=true`、`message`
- **AND** 响应体 MUST NOT 包含 `data` 字段（不得返回 `data=null`）

#### Scenario: error_response 返回一致结构

- **GIVEN** 任意业务接口发生业务错误
- **WHEN** 返回 `error_response(code, message)`
- **THEN** 响应体包含 `success=false`、`error.code`、`error.message`

### Requirement: 对外成功响应必须使用平台 success_response/paged_response

系统对外 API 在返回成功结果时 MUST 使用 `platform_core.response.success_response` 或 `platform_core.response.paged_response` 生成响应体，避免上下文之间出现成功信封语义漂移。

#### Scenario: 业务成功返回标准成功信封（带 data）

- **GIVEN** 任意业务接口执行成功且需要返回业务数据
- **WHEN** 返回 `success_response(data, message)`
- **THEN** 响应体包含 `success=true`
- **AND** 响应体包含 `message`
- **AND** 响应体包含 `data`

#### Scenario: 业务成功返回标准成功信封（无 data）

- **GIVEN** 任意业务接口执行成功但不需要返回业务数据
- **WHEN** 返回 `success_response(message=...)`（或 `success_response()`）
- **THEN** 响应体包含 `success=true`
- **AND** 响应体包含 `message`
- **AND** 响应体 MUST NOT 包含 `data` 字段
