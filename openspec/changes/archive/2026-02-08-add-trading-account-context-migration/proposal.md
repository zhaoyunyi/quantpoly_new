## Why

交易账户、持仓、订单、资金流水是风险控制、信号执行、实时监控的基础数据层。源项目该领域代码体量较大且接口较散，需要在当前仓库先抽象成可复用库，再以统一规范接入。

## What Changes

- 新增 `trading-account` capability：
  - 账户生命周期管理（创建、激活、停用、删除）；
  - 持仓/交易记录/资金流水查询与统计；
  - 统一 user ownership 校验。
- 要求 repository/service 显式 `user_id` 参数，杜绝隐式全局查询。

## Impact

- 新增 capability：`trading-account`
- 依赖 capability：`user-auth`、`backend-user-ownership`、`platform-core`
- 被依赖 capability：`risk-control`、`signal-execution`、`monitoring-realtime`

