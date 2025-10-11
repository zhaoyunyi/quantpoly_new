# Change: success_response 的 data 字段在无返回数据时可省略

## Why

当前实现 `platform_core.response.success_response` 在 `data is None` 时不会输出 `data` 字段；但 `openspec/specs/platform-core/spec.md` 仍将 `data` 描述为必有字段，导致规范与实现/迁移 Runbook 不一致。

本变更用于将规范对齐到已落地实现，减少调用方与各 bounded context 之间的契约歧义。

## What Changes

- **BREAKING**：更新 `platform-core` 规范：`success_response` 在无数据返回时 `data` 字段 MUST 省略（而不是 `null`）。
- 补充 BDD 场景，覆盖“有 data”与“无 data”两种成功响应。
- 更新 `platform_core` 单元测试，锁定该行为。

## Impact

- Affected specs: `platform-core`
- Affected code: `libs/platform_core/tests/test_response.py`
- Affected clients: 调用方需要健壮处理 `success=true` 但 `data` 缺省的成功响应（已在 runbook 中提示）
