## 1. 风险与信号 sqlite 适配器移除

- [x] 1.1 risk-control：删除 sqlite 仓储与 sqlite 测试
- [x] 1.2 signal-execution：删除 sqlite 仓储与 sqlite 测试

## 2. 集成收敛

- [x] 2.1 更新两个库 `__init__` 导出面
- [x] 2.2 运行风险与信号上下文测试集
- [x] 2.3 运行 composition 与全量 `pytest`
- [x] 2.4 `openspec validate remove-sqlite-risk-signal-adapters --strict`
