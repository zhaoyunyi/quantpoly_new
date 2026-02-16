## Why

用户已确认采用 **C（硬切 PostgreSQL）** 路线：不再保留 SQLite 作为后端运行时持久化后端。

当前主干仍存在以下问题：

- 组合入口 `storage_backend` 仍是 `sqlite|memory`，与目标架构不一致；
- 风控/信号/偏好等能力规范仍以 sqlite 为持久化默认，导致运行时治理目标与规格漂移；
- wave0 中已存在部分可复用 Postgres 适配器实现，但尚未统一接入当前组合入口。

为避免长期双路径导致的行为漂移，本变更将后端运行时持久化主路径统一为 PostgreSQL（允许 memory 仅用于测试）。

## What Changes

- 组合入口配置从 `sqlite|memory` 调整为 `postgres|memory`；
- 引入并接入 Postgres 持久化适配器（优先迁移 wave0 已验证模块）；
- 移除 backend_app 对 sqlite 运行时参数与装配分支；
- 更新 CLI 与配置协议：使用 `postgresDsn/BACKEND_POSTGRES_DSN`；
- 调整 OpenSpec 中涉及 sqlite 运行时主路径的需求描述为 postgres。

## Impact

- 影响 capability：`platform-core`、`user-preferences`、`risk-control`、`signal-execution`
- 影响代码：`apps/backend_app/*` 与相关上下文 repository adapter 装配
- 破坏性变更：
  - `BACKEND_STORAGE_BACKEND=sqlite` 不再支持；
  - `BACKEND_SQLITE_DB_PATH` 与 `sqliteDbPath` 输入不再生效。
- 保留项：`memory` 模式仅用于测试/开发自检，不作为生产持久化路径。
