## 1. 需求与合同（Spec）

- [ ] 1.1 增加 `backtest-runner` 引擎执行需求 delta（含场景）
- [ ] 1.2 增加 API 合同测试：提交任务后返回指标与结果读取
- [ ] 1.3 增加 CLI 合同测试：回测执行与 JSON 输出

## 2. 引擎与存储（Library-First）

- [ ] 2.1 增加 `BacktestResultStore`（in-memory + sqlite）
- [ ] 2.2 实现最小回测引擎（先覆盖 moving_average/mean_reversion）
- [ ] 2.3 计算并回填 `BacktestTask.metrics`

## 3. API/编排

- [ ] 3.1 更新 `/backtests/tasks`：执行引擎、处理失败、写入 job error
- [ ] 3.2 增加结果读取 API：`GET /backtests/{taskId}/result`

## 4. 验证

- [ ] 4.1 运行相关 pytest
- [ ] 4.2 运行 `openspec validate update-backtest-engine-parity --type change --strict`
