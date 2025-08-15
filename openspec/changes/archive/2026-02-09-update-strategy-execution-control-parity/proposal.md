## Why

源项目 `strategy_execution.py` 提供了执行引擎控制面：参数校验、信号生成、执行处理、运行中视图与趋势统计。当前仓库虽具备 `signal-execution` 的批处理与维护接口，但缺少这部分“执行前/执行中控制能力”。

若不补齐，策略域将停留在“信号后处理”，无法形成完整“策略参数 -> 信号生成 -> 执行控制 -> 统计分析”闭环。

## What Changes

- 扩展 `signal-execution`：
  - 增加策略参数校验与信号生成接口；
  - 增加执行处理、执行详情、运行中执行列表；
  - 增加执行趋势与策略统计视图。
- 扩展 `strategy-management`：
  - 增加策略执行前校验挂接点，保证模板参数一致性。

## Impact

- Affected specs:
  - `signal-execution`
  - `strategy-management`
- Affected code:
  - `libs/signal_execution/*`
  - `libs/strategy_management/*`
