## 1. 需求与合同（Spec）

- [ ] 1.1 增加回测重命名需求 delta（含场景）
- [ ] 1.2 增加相关回测查询需求 delta（含场景）
- [ ] 1.3 增加 API/CLI 合同测试（重命名/相关查询）

## 2. Library-First 实现

- [ ] 2.1 在 `BacktestService` 增加重命名与相关查询服务方法
- [ ] 2.2 在 repository 增加同策略关联查询能力
- [ ] 2.3 补齐 CLI 命令（rename / related）

## 3. API

- [ ] 3.1 增加 `PATCH /backtests/{taskId}/name`
- [ ] 3.2 增加 `GET /backtests/{taskId}/related`

## 4. 验证

- [ ] 4.1 运行 `pytest -q libs/backtest_runner/tests`
- [ ] 4.2 运行 `openspec validate update-backtest-management-readmodel-parity --type change --strict`
