## Why

当前 `signal-execution` 的 `generate_signals` 仅按请求传入的 `symbols` 创建信号记录，本质是“录入工具”，并不基于策略模板与市场数据进行评估。
而源项目的 `StrategyExecutionService` 与产品愿景都要求：用户选择策略模板 + 参数后，系统能够自动评估市场数据并生成可处理的 BUY/SELL 信号，形成研究与模拟交易闭环。

如果继续保持“手工创建信号”的方式：

- 策略模板无法转化为可执行逻辑（体验断层）；
- 回测与模拟交易只能依赖外部注入结果，无法验证“端到端一致性”；
- 不同上下文可能各自实现策略评估逻辑，导致口径不一致。

## What Changes

- 为 `signal-execution` 增加“策略驱动生成”路径：从 `strategyId + accountId` 出发，读取策略模板/参数并拉取市场历史数据，计算指标后决定是否生成信号。
- 引入跨上下文 ACL：通过注入的 `strategy_reader` / `market_history_reader` 获取必要信息，避免跨域直连仓储。
- 补齐 API/CLI 合同测试：验证策略 inactive 时不生成、数据不足时跳过、成功时生成结构化信号。

## Impact

- Affected specs:
  - `signal-execution`
- Affected code:
  - `libs/signal_execution/*`
- Dependencies:
  - `strategy-management`（策略模板与参数 schema）
  - `market-data`（历史行情与指标计算）
