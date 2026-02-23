## Why

当前能力规格存在“标题写 sqlite、正文写 postgres”的语义冲突，且 `openspec/project.md` 仍保留 SQLite/D1 作为运行期路线描述，不符合已完成的 PostgreSQL 硬切事实。

## What Changes

- 统一 `user-preferences`、`risk-control`、`signal-execution` 三个 capability 的持久化 requirement 命名与描述为 postgres；
- 更新 `openspec/project.md` 技术栈与外部依赖描述，移除 SQLite/D1 运行期路线表达；
- 保持其余能力行为不变，仅做规范真相收敛。

## Impact

- 影响 capability：`user-preferences`、`risk-control`、`signal-execution`
- 影响文档：`openspec/project.md`
- 兼容性：无运行时行为变化，仅规范一致性修复
