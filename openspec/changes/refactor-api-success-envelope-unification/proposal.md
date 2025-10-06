## Why

当前成功响应虽大多包含 `success=true` 与 `data`，但仍存在“手写响应结构”与“message 字段不一致”的情况。

在允许 break update 的策略下，建议把成功响应也纳入平台契约治理：使用 `platform_core.response` 作为唯一权威构造器，降低路由层语义漂移与重复劳动。

## What Changes

- 明确成功响应的权威结构：
  - `success_response(data, message)`
  - `paged_response(items, total, page, page_size)`
- 将组合入口（`backend_app`）与 `user-auth` 中的手写成功响应逐步替换为上述构造器。
- 补齐/统一关键成功响应的 `message` 字段（默认值可为 `ok`）。

## Impact

- 影响 capability：`platform-core`、`user-auth`、`backend-app`
- **BREAKING（轻）**：部分成功响应会新增或标准化 `message` 字段；HTTP status code 不变。

