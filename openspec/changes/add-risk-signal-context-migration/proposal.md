## Why

源项目中 `risk_control`、`signals`、`strategy_execution` 存在较多“已认证但未按用户过滤”的接口，形成越权面。该领域同时依赖策略与交易账户数据，需在中后期独立迁移并强化权限边界。

## What Changes

- 新增 `risk-control` capability：
  - 风控规则 CRUD、适用规则计算、报警处理；
  - 批量确认/解决/统计接口全部用户隔离。
- 新增 `signal-execution` capability：
  - 信号查询、执行、取消、批处理、搜索；
  - 策略执行记录与趋势统计；
  - 禁止全局清理/全局趋势等越权操作。

## Impact

- 新增 capability：`risk-control`、`signal-execution`
- 依赖 capability：`strategy-management`、`backtest-runner`、`trading-account`、`user-auth`
- 直接降低安全风险：收敛批处理与统计接口越权面

