## ADDED Requirements

### Requirement: 对外成功响应必须使用平台 success_response/paged_response

系统对外 API 在返回成功结果时 MUST 使用 `platform_core.response.success_response` 或 `platform_core.response.paged_response` 生成响应体，避免上下文之间出现成功信封语义漂移。

#### Scenario: 业务成功返回标准成功信封

- **GIVEN** 任意业务接口执行成功
- **WHEN** 返回成功结果
- **THEN** 响应体包含 `success=true`
- **AND** 响应体包含 `data`

