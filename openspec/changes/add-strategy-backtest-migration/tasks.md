## 1. strategy-management 库

- [x] 1.1 新建 `libs/strategy_management` 并定义领域模型与仓储接口
- [x] 1.2 实现策略 CRUD 与模板参数校验 CLI
- [x] 1.3 实现删除前回测占用检查并补充 409 场景测试

## 2. backtest-runner 库

- [x] 2.1 新建 `libs/backtest_runner` 并定义回测任务聚合与状态机
- [x] 2.2 实现任务创建/查询/取消接口与 CLI
- [x] 2.3 增加状态轮询与广播事件契约测试

## 3. 集成与验证

- [x] 3.1 将路由接入统一 `get_current_user` 与所有权校验
- [x] 3.2 保证 API envelope 与 camelCase 输出一致
- [x] 3.3 运行 `pytest -q` 与 `openspec validate add-strategy-backtest-migration --strict`
