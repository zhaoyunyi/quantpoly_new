## Why

源项目在风控与信号执行提供了较完整的规则、筛选、批处理与维护能力；当前仓库 `risk-control` 与 `signal-execution` 仅保留最小接口，无法支撑“规则治理 → 信号执行 → 风险反馈”闭环。

同时，批量维护类接口天然具备高风险，需要严格治理与审计。

## What Changes

- 扩展 `risk-control`：
  - 风险规则 CRUD、启停、适用规则查询；
  - 账户/策略风险评估与仪表盘视图；
  - 告警查询、确认、解决、批量处理。
- 扩展 `signal-execution`：
  - 信号筛选、搜索、批量执行/取消；
  - 执行记录查询与趋势统计；
  - 过期信号维护任务。
- 治理约束：
  - 高风险维护接口仅管理员可调用，且必须审计。

## Impact

- Affected specs:
  - `risk-control`
  - `signal-execution`
  - `admin-governance`（间接受益）
- Affected code:
  - `libs/risk_control/*`
  - `libs/signal_execution/*`
  - `libs/admin_governance/*`（高风险动作治理接入）
