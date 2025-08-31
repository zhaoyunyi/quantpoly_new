## Why

当前策略/信号域已具备基础 CRUD 与批处理，但仍缺少源项目中的“策略驱动信号生成、单信号处理、执行历史清理、策略研究自动化”能力。
这会导致策略研究链路停留在手工操作，无法形成稳定的自动化闭环。

## What Changes

- 补齐策略驱动信号生成/处理的统一语义与错误码。
- 补齐执行历史保留与清理策略（含审计语义）。
- 增加策略绩效分析与优化建议任务化能力。

## Impact

- Affected specs:
  - `strategy-management`
  - `signal-execution`
- Affected code:
  - `libs/strategy_management/*`
  - `libs/signal_execution/*`
  - `libs/job_orchestration/*`
