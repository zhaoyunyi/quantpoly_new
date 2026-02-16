## 1. 风险与信号 sqlite 适配器移除

- [ ] 1.1 risk-control：删除 sqlite 仓储与 sqlite 测试
- [ ] 1.2 signal-execution：删除 sqlite 仓储与 sqlite 测试

## 2. 集成收敛

- [ ] 2.1 更新两个库 `__init__` 导出面
- [ ] 2.2 运行风险与信号上下文测试集
- [ ] 2.3 运行 composition 与全量 `pytest`
- [ ] 2.4 `openspec validate remove-sqlite-risk-signal-adapters --strict`
