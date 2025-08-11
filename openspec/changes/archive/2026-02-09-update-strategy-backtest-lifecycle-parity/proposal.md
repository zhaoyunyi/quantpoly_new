## Why

源项目在策略与回测上提供了较完整的生命周期能力（模板、激活/停用、回测统计、任务状态、结果对比），而当前仓库仅覆盖基础 CRUD 与任务查询骨架，能力深度不足。

在产品愿景中，策略研究闭环必须包含：
- 策略配置与模板复用；
- 回测任务提交与状态跟踪；
- 回测结果统计与策略间对比。

因此需要将 `strategy-management` 与 `backtest-runner` 从“可用骨架”升级到“可研究闭环”。

## What Changes

- 扩展 `strategy-management`：
  - 模板列表与模板实例化；
  - 策略状态机（draft/active/inactive/archived）；
  - 策略激活/停用与参数校验。
- 扩展 `backtest-runner`：
  - 回测列表、统计、结果对比；
  - 任务取消/失败重试语义；
  - 与 `job-orchestration` 的任务追踪对齐。

## Impact

- Affected specs:
  - `strategy-management`
  - `backtest-runner`
  - `job-orchestration`（间接受益）
- Affected code:
  - `libs/strategy_management/*`
  - `libs/backtest_runner/*`
  - `libs/job_orchestration/*`（任务追踪适配）
