## Why

当前后端仍允许通过 `current_user.is_admin=true` 这种 legacy 字段绕过管理员判定。
在“允许 break update，但功能不能缺失”的迁移策略下，继续保留该分支会导致：

- 管理员语义漂移（同一套系统出现 role/level/is_admin 多种来源）
- 风险面扩大（误注入 `is_admin` 字段可能导致越权）
- 测试与实现复杂度持续上升

## What Changes

- 移除 `platform_core.authz.resolve_admin_decision()` 对 `actor.is_admin` 的兼容判定。
- 管理员判定统一来源：`role=admin`（以及现有 `level>=10` 兜底逻辑保持不变）。
- 交易运维（trading ops）与信号维护（signal maintenance）接口不再接受 legacy `is_admin` 作为管理员输入。

## Impact

- 影响 capability：`platform-core`
- 连带影响：`trading-account`、`signal-execution`
- break update：旧测试/旧客户端若仍注入 `is_admin` 字段将被拒绝（403/ADMIN_REQUIRED）

## Break Update 迁移说明

- **不再支持**：通过 `current_user.is_admin=true` 触发管理员权限。
- 客户端/组合层必须迁移为：
  - `current_user.role=admin`（推荐）
  - 或维持既有 `level>=10` 兜底（如确有需要）
