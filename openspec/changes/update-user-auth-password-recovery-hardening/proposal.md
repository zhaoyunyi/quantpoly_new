## Why

当前密码找回流程可用但仍存在生产化缺口：重置 token 采用内存存储，且 request 接口直接返回 token。
这在服务重启恢复、安全审计与抗枚举策略上均不充分。

## What Changes

- 将密码找回 token 改为持久化与受控失效策略（TTL + 单次消费）。
- request 接口不再返回明文 reset token，改为统一成功响应与审计事件。
- 明确密码找回的频控、抗枚举和失败错误语义。
- 保持 break update：不兼容旧的“直接返回 token”行为。

## Impact

- 影响 capability：`user-auth`
- 关联模块：`user_auth`、`platform_core`（日志/审计）
- 风险：测试与联调脚本需要从“token 直出”迁移到“受控投递/测试钩子”
