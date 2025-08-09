## 1. 持久化适配器落地

- [x] 1.1 为 trading-account 提供持久化 repository adapter
- [x] 1.2 为 strategy-management 提供持久化 repository adapter
- [x] 1.3 为 backtest-runner 提供持久化 repository adapter
- [x] 1.4 为 job-orchestration 提供持久化 repository adapter

## 2. 事务与幂等

- [ ] 2.1 引入 Unit of Work 事务边界并覆盖关键写流程
- [ ] 2.2 引入 idempotency key 唯一约束与冲突错误语义
- [x] 2.3 覆盖并发提交、重试、回滚测试场景

## 3. 切换与验证

- [ ] 3.1 将 in-memory 从生产主路径降级为测试替身
- [x] 3.2 增加重启恢复能力验证
- [ ] 3.3 运行 `openspec validate update-persistence-adapters-uow --strict`
