## Why

当前 `backtest-runner` 已具备任务执行与结果读取能力，但与源项目后端相比，回测“管理读模型”仍有缺口：

- 缺少回测名称重命名能力（用于研究过程中标注实验版本）；
- 缺少同策略相关回测聚合查询（用于快速横向对比历史实验）。

这些能力属于回测研究闭环的运营层需求，不依赖前端兼容路径，但能显著提升可用性与复盘效率。

## What Changes

- 为 `backtest-runner` 增加回测元数据管理能力：支持重命名。
- 增加相关回测查询能力：按同策略聚合、可排除当前任务、支持状态过滤与数量限制。
- 补齐 API/CLI 合同测试，覆盖所有权校验与边界行为。

## Impact

- Affected specs:
  - `backtest-runner`
- Affected code:
  - `libs/backtest_runner/*`
- Dependencies:
  - `strategy-management`（用于策略维度关联）
