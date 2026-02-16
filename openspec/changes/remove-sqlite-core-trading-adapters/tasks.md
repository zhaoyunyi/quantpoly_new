## 1. 核心上下文 sqlite 适配器移除

- [ ] 1.1 strategy-management：删除 sqlite 仓储与 sqlite 测试
- [ ] 1.2 backtest-runner：删除 sqlite 仓储/结果存储与 sqlite 测试
- [ ] 1.3 job-orchestration：删除 sqlite 仓储与 sqlite 测试
- [ ] 1.4 trading-account：删除 sqlite 仓储与 sqlite 测试

## 2. 集成收敛

- [ ] 2.1 更新四个库 `__init__` 导出面
- [ ] 2.2 运行四个上下文测试集
- [ ] 2.3 运行 composition 与全量 `pytest`
- [ ] 2.4 `openspec validate remove-sqlite-core-trading-adapters --strict`
