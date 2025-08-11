## 1. Strategy 生命周期能力

- [x] 1.1 增加策略模板读取与模板实例化能力
- [x] 1.2 增加策略状态机与迁移约束（draft/active/inactive/archived）
- [x] 1.3 增加策略参数校验与错误码映射

## 2. Backtest 读写能力补齐

- [x] 2.1 增加回测列表、分页、筛选
- [x] 2.2 增加回测统计接口（收益、回撤、胜率等）
- [x] 2.3 增加回测结果对比接口（多任务）
- [x] 2.4 增加任务取消/重试语义与状态追踪

## 3. 任务编排对齐

- [x] 3.1 回测任务提交接入统一任务编排接口（`JobOrchestrationBacktestDispatcher`）
- [x] 3.2 接入幂等键并定义冲突语义
- [x] 3.3 验证任务越权读取返回 403

## 4. 测试与校验

- [x] 4.1 按 TDD 增加策略/回测领域与 API/CLI 测试
- [x] 4.2 覆盖策略删除占用检查与回测对比场景
- [x] 4.3 运行 `openspec validate update-strategy-backtest-lifecycle-parity --strict`
