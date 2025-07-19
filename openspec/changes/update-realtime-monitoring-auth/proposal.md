# 提案：update-realtime-monitoring-auth

## Why（为什么要做）

旧项目 `monitoring-realtime` spec 明确依赖 better-auth 会话（cookie `session_token`）进行 WebSocket 认证。但迁移目标已确定为 A：**后端自管用户系统**，不再使用 better-auth。

因此需要更新实时监控（WebSocket）能力的认证方式，使其与新 `user-auth` 一致，避免：

- spec 与实现脱节
- 不同通道（HTTP vs WS）使用不同 token 体系

## What Changes（做什么）

- 新增 `update-realtime-monitoring-auth` change，对 `monitoring-realtime` capability 做增量修改：
  - `/ws/monitor` 认证从 better-auth 迁移为后端 session token（cookie 或 bearer）
  - 明确未认证关闭码、token 传递方式优先级

## Impact（影响）

- 统一 HTTP 与 WebSocket 的鉴权语义
- 为监控/推送模块并行迁移扫清依赖阻塞

