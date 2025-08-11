# update-persistence-adapters-uow 设计说明

## 1. 设计目标

将核心上下文从 in-memory 主路径升级为持久化主路径，并引入 Unit of Work（UoW）统一事务边界，确保硬切换后的数据可恢复性、并发一致性与幂等性。

## 2. 范围

- 上下文：`trading-account`、`strategy-management`、`backtest-runner`、`job-orchestration`
- 能力：持久化仓储适配器、事务边界、幂等键唯一约束、冲突语义
- 非目标：一次性覆盖所有上下文的全量物理建模（可分波次推进）

## 3. 架构设计

## 3.1 仓储分层

- **Domain Port**：上下文定义仓储接口（不依赖具体数据库）
- **Persistence Adapter**：按边界实现 Postgres/D1 适配器
- **Test Double**：保留 in-memory 作为测试替身

## 3.2 Unit of Work

- 一个业务写请求对应一个 UoW；
- UoW 负责 begin/commit/rollback；
- 同一事务内保证聚合更新原子性。

## 3.3 幂等机制

- 关键写路径（任务提交、回测创建、交易提交）引入 `idempotencyKey`；
- 存储层施加唯一约束；
- 冲突时返回明确错误语义（非 500）。

## 4. 数据边界与上下文隔离

- 严格遵守 `data-topology-boundary` 约束；
- 跨库访问通过 ACL/防腐层，不做仓储层直连跨界。

## 5. 落地策略

1. 为 4 个上下文补齐持久化 adapter；
2. 在 service 层引入 UoW 协议；
3. 替换生产主路径为持久化实现；
4. 通过重启恢复与并发冲突测试。

## 6. 测试策略（TDD导向）

- Red：先写并发冲突、重启恢复、事务回滚失败用例；
- Green：最小实现通过；
- Refactor：统一错误码与日志输出。

## 7. 风险与缓解

- 风险：迁移阶段双实现并存导致行为不一致。
  - 缓解：明确主路径标识，in-memory 仅测试使用。
- 风险：事务边界定义不一致。
  - 缓解：统一 UoW 约定并在代码审查中强制检查。
- 风险：幂等键策略覆盖不全。
  - 缓解：关键写接口逐一建立幂等清单。

## 8. 交付物

- 四个上下文持久化适配器设计
- UoW 协议与事务边界清单
- 幂等键约束与冲突语义规范
