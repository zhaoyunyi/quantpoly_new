## Why

源项目存在 D1/SQLite 与 PostgreSQL 双数据库拓扑，且通过 `database_router` 按模型路由，策略等模型曾在用户库与业务库之间迁移，边界不够稳定：

- `quantpoly-backend/backend/app/core/database_router.py`
- `quantpoly-backend/backend/app/core/db.py`

若不先明确数据拓扑边界，后续迁移将反复出现跨库耦合、事务边界不清、读写一致性问题。

## What Changes

- 新增 `data-topology-boundary` capability：
  - 定义“用户域库”与“业务域库”的最终边界清单；
  - 定义跨库访问规则（禁止跨库 join、通过 ACL/anti-corruption 接口交互）；
  - 定义迁移脚本/回填/回滚标准；
  - 定义一致性策略（最终一致 + 补偿机制）。
- 输出库级别 CLI 校验工具（边界审查、模型归属检查、迁移 dry-run）。

## Impact

- 新增 capability：`data-topology-boundary`
- 依赖 capability：`platform-core`、`user-auth`
- 被依赖 capability：`strategy-management`、`backtest-runner`、`trading-account`、`risk-control`、`signal-execution`

