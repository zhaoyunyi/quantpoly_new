# remove-sqlite-runtime-hard-cutover 设计说明

## 1. 目标

将后端运行时持久化统一到 PostgreSQL，消除 sqlite 主路径，确保组合入口能力与目标生产架构一致。

## 2. 范围与非目标

### 范围
- 组合根配置协议（settings/CLI/app/router）
- 运行时 repository adapter 装配路径
- 对应 OpenSpec 需求文本修正（sqlite -> postgres）

### 非目标
- 一次性删除所有 sqlite 历史代码文件（可保留用于回溯与过渡测试）
- 一次性引入复杂迁移框架（先保证功能完整与路径统一）

## 3. 架构决策

1. `storage_backend` 只接受 `postgres|memory`
2. `postgres` 需要显式 DSN（`BACKEND_POSTGRES_DSN` 或 CLI 入参）
3. `memory` 仅用于测试（组合测试与单测），非生产默认
4. 各上下文保持 Library-First：优先新增 `repository_postgres.py`，不在 service 层硬编码数据库细节

## 4. 失败策略

- 缺失 postgres DSN：启动失败（fail-fast）
- 非法 backend/provider：启动失败并返回可识别错误

## 5. 验证策略

- 组合根装配测试：`postgres` 分支选用 Postgres adapter，`memory` 分支保持测试替身
- CLI 解析测试：`postgresDsn` 输入/环境变量优先级正确
- OpenSpec 严格校验：`openspec validate remove-sqlite-runtime-hard-cutover --strict`
