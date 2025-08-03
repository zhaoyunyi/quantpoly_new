# signal-execution Specification

## Purpose
TBD - created by archiving change add-risk-signal-context-migration. Update Purpose after archive.
## Requirements
### Requirement: 信号与执行记录接口必须强制用户范围
信号查询、批处理、执行记录查询与取消 MUST 在服务端强制按当前用户过滤。

#### Scenario: 越权 signal_id 执行被拒绝
- **GIVEN** 信号不属于当前用户
- **WHEN** 调用执行或取消接口
- **THEN** 返回 403
- **AND** 信号状态不得发生变更

### Requirement: 维护类接口不得进行全局删除/更新
清理过期信号、清理旧执行记录等维护接口 MUST 限定用户作用域或仅限管理员角色。

#### Scenario: 普通用户调用全局清理接口
- **GIVEN** 普通用户已认证
- **WHEN** 调用清理接口
- **THEN** 返回 403
- **AND** 不应删除其他用户数据

