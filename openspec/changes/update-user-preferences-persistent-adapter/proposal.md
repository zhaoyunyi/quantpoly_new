## Why

偏好系统当前在组合入口仍默认 InMemory，无法满足“重启不丢偏好”的基础体验。
需要把偏好存储接入可持久化适配器并纳入统一装配。

## What Changes

- 为 `user-preferences` 增加 sqlite 持久化适配器并接入组合入口。
- 保持偏好版本迁移、深度合并、权限校验语义不变。
- 补齐 CLI 与测试。

## Impact

- 影响 capability：`user-preferences`
- 依赖：`update-runtime-persistence-provider-baseline`
