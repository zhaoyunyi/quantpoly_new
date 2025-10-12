# Change: 清理剩余 legacy 兼容层（BREAK UPDATE）

## Why

当前仓库已完成 Wave0~Wave7 的后端能力迁移并归档，允许 break update，但要求功能不缺失。

在“功能缺口清零”后，仍存在少量迁移期遗留的 **legacy 兼容字段/分支**（例如任务类型注册表返回 `legacyNames`），会：

- 让客户端误以为仍需理解旧系统命名
- 增加接口契约噪音，造成 spec / 实现 / 调用方理解偏差
- 放大后续治理成本（每次改动都要考虑 legacy 字段）

因此需要在 P1 治理阶段进行一次明确的 break update：移除这些迁移期兼容表面，收敛到单一权威契约。

## What Changes

- **BREAKING**：`job-orchestration` 的任务类型注册表输出移除 `legacyNames` 字段，仅保留权威字段（`taskType/domain/schedulable`）。
- 更新测试与 OpenSpec 规范，锁定该契约。

## Impact

- Affected specs: `job-orchestration`
- Affected code:
  - `libs/job_orchestration/job_orchestration/task_registry.py`
  - `libs/job_orchestration/tests/test_api_domain_task_parity.py`
- Affected clients: 若客户端/脚本依赖 `legacyNames`，需要移除该依赖（使用 `taskType` 作为唯一权威标识）。
