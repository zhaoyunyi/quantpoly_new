# add-platform-core Tasks

## 1. 规范与目录

- [x] 1.1 创建 capability `platform-core` 的 spec（`openspec/specs/platform-core/spec.md`）
- [x] 1.2 为 `platform-core` 建立最小设计约束（`openspec/specs/platform-core/design.md`，如需要）— 当前无需额外 design.md

## 2. 代码落地（后续执行阶段）

> 说明：本次只提交变更提案与需求；实现阶段遵循 `spec/ProgramSpec.md` 严格 TDD。

- [x] 2.1 创建 `platform_core` Python library（配置、日志、错误、响应）
- [x] 2.2 提供 CLI：`platform-core`（stdin/args/files；stdout；支持 JSON）
- [x] 2.3 添加单元测试与 BDD 输出示例

