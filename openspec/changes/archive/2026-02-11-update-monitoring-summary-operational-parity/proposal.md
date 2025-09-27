## Why

当前监控摘要已覆盖信号/告警基础统计，但运营视角指标仍不足（任务运行态、活跃策略、回测运行态、账户覆盖等）。
这使监控首屏与旧系统运维语义不完全对齐，也影响异常定位效率。

## What Changes

- 扩展 `/monitor/summary` 为运营读模型，补齐账户/策略/回测/任务核心指标。
- 统一 WS 推送与 REST 摘要在关键字段上的口径定义。
- 引入跨上下文读取协议（ACL/OHS），避免监控层直接耦合内部仓储。
- 采用 break update，允许调整摘要字段结构以达成统一语义。

## Impact

- 影响 capability：`monitoring-realtime`
- 依赖：`job-orchestration` 任务状态语义
- 关联模块：`strategy-management`、`backtest-runner`、`trading-account`、`signal-execution`、`risk-control`
