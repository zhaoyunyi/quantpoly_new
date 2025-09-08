## 1. 需求与合同（Spec）

- [x] 1.1 增加回测重命名需求 delta（含场景）
- [x] 1.2 增加相关回测查询需求 delta（含场景）
- [x] 1.3 增加 API/CLI 合同测试（重命名/相关查询）

## 2. Library-First 实现

- [x] 2.1 在 `BacktestService` 增加重命名与相关查询服务方法
- [x] 2.2 在 repository 增加同策略关联查询能力
- [x] 2.3 补齐 CLI 命令（rename / related）

## 3. API

- [x] 3.1 增加 `PATCH /backtests/{taskId}/name`
- [x] 3.2 增加 `GET /backtests/{taskId}/related`

## 4. 验证

- [x] 4.1 运行 `pytest -q libs/backtest_runner/tests`
- [x] 4.2 运行 `openspec validate update-backtest-management-readmodel-parity --type change --strict`
