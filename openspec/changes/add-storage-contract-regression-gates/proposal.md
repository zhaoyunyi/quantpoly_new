## Why

虽然当前已完成 sqlite 运行时硬切，但缺少统一、可自动执行的门禁，未来改动仍可能把 sqlite 导出路径回流到库公开面。

## What Changes

- 在 `platform-core` 增加 `storage-contract-gate` 能力（CLI + 评估逻辑）；
- 默认校验核心上下文库公开导出（`__all__`）不包含 sqlite 适配器命名；
- 支持 JSON 输入（stdin/args/file）以便 CI 与本地自定义门禁执行。

## Impact

- 影响 capability：`platform-core`
- 影响代码：`platform_core.cli` 与新增门禁评估模块
- 兼容性：新增能力，不改变现有业务 API
