## ADDED Requirements

### Requirement: 后端必须提供单一组合入口
系统 MUST 提供单一后端组合入口来装配所有 bounded context 的 REST 与 WS 能力，作为发布、切换、回滚的唯一控制点。

#### Scenario: 通过单一入口装配全部上下文
- **GIVEN** 系统存在多个已迁移上下文能力
- **WHEN** 启动后端服务
- **THEN** 所有对外 API 与 WS 能力必须由统一组合入口装配并对外可用
- **AND** 不得要求调用方分别连接多个分散入口

### Requirement: 组合入口必须统一横切策略
组合入口 MUST 统一鉴权、错误信封与日志脱敏策略，避免上下文之间出现语义漂移。

#### Scenario: 不同上下文返回一致错误语义
- **GIVEN** 两个不同业务上下文发生权限错误
- **WHEN** 客户端请求被拒绝
- **THEN** 错误响应结构与脱敏日志行为必须一致
- **AND** 不得泄露明文 token/cookie 等敏感字段
