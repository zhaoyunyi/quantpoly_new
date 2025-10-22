## 1. `/backtests` 列表页

- [x] 1.1 列表对接：`GET /backtests?page&pageSize&status&strategyId`
- [x] 1.2 统计对接：`GET /backtests/statistics`
- [x] 1.3 创建回测：
  - [x] 最小表单：strategyId + config（时间范围/初始资金/标的/频率）
  - [x] 提交方式 A：`POST /backtests`
  - [x] 提交方式 B（可选）：`POST /backtests/tasks` 返回 job 以及 backtestTask
- [x] 1.4 运行中任务提示：轮询 `GET /backtests` 或按 job 状态
- [x] 1.5 批量/单项操作：取消、重试、删除、重命名

## 2. `/backtests/$id` 详情页

- [x] 2.1 详情对接：`GET /backtests/{id}`
- [x] 2.2 结果对接：`GET /backtests/{id}/result`
  - [x] 处理 404 `BACKTEST_RESULT_NOT_READY`：展示"未就绪"并提供刷新
- [x] 2.3 相关回测：`GET /backtests/{id}/related`
- [x] 2.4 操作：取消/重试/重命名

## 3. 对比

- [x] 3.1 在列表页支持选择多个 backtest taskId
- [x] 3.2 调用 `POST /backtests/compare` 展示对比表（与策略对比复用组件）

## 4. 组件规划

- [x] 4.1 `BacktestTable`
- [x] 4.2 `BacktestCreateDialog`
- [x] 4.3 `BacktestStatusBadge`
- [x] 4.4 `BacktestResultPanel`（指标卡 + 图表占位）
- [x] 4.5 `BacktestActions`（cancel/retry/rename）

## 5. 测试（TDD）

- [x] 5.1 单元测试：result 未就绪时展示"刷新/轮询"提示
- [x] 5.2 单元测试：compare 选中数量与提交参数正确

## 6. 回归验证

- [x] 6.1 `cd apps/frontend_web && npm run build`
- [x] 6.2 `pytest -q`
