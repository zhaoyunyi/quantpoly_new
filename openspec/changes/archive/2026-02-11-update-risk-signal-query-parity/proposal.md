## Why

当前 `risk-control` 与 `signal-execution` 主链路已具备，但在运营查询面仍存在可用性缺口：

- 风控缺少规则统计与近期告警快捷视图；
- 信号缺少手动过期操作与账户维度统计入口。

这些缺口不影响核心交易流程，但会显著增加运营排障与监控页面拼装复杂度。

## What Changes

- 风控域增加规则统计、近期告警与未解决告警快捷查询。
- 信号域增加手动过期接口与账户维度统计查询。
- 补齐 API/CLI 合同测试与权限测试。

## Impact

- Affected specs:
  - `risk-control`
  - `signal-execution`
- Affected code:
  - `libs/risk_control/*`
  - `libs/signal_execution/*`
- Dependencies:
  - `monitoring-realtime`（监控摘要可直接复用快捷查询）
