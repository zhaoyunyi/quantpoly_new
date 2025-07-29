## Why

源项目在多个业务域暴露“管理类/维护类”能力（如全局清理、批量维护、超级用户操作），但权限边界并不稳定，部分接口仅做认证未做严格授权，存在误操作与越权风险。

示例问题：

- 普通用户可触发全局清理语义接口：`strategy_execution.py`、`signals.py`
- 管理员能力分散在业务路由，审计与风控难统一

需要独立建立“管理员治理上下文”，避免把治理逻辑散落到各业务 capability。

## What Changes

- 新增 `admin-governance` capability：
  - 管理员能力目录（capability + action 白名单）；
  - 统一授权中间层（role/level/policy）；
  - 高风险操作二次确认令牌；
  - 管理员操作审计日志（actor/action/target/result）。
- 业务域仅声明“需要何种治理动作”，不自行实现鉴权细节。

## Impact

- 新增 capability：`admin-governance`
- 依赖 capability：`user-auth`、`platform-core`
- 被依赖 capability：`trading-account`、`signal-execution`、`risk-control`、`monitoring-realtime`

