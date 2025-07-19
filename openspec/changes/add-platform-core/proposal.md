# 提案：add-platform-core

## Why（为什么要做）

旧项目后端（FastAPI）在“配置 / 数据库会话 / 响应结构 / 日志与错误处理 / 字段命名规范”等方面存在不一致与隐式约定，导致：

- 迁移时每个模块都要重复造轮子
- API 响应格式难以统一（尤其 `camelCase` 规范）
- 测试与 CLI 可观测性不足，难以满足 `spec/ProgramSpec.md` 的 Library-First + CLI + Test-First

因此需要先在新仓库建立 **平台基础能力**，为后续并行迁移各 bounded context（策略/回测/交易/风控/监控等）提供一致的“地基”。

## What Changes（做什么）

- 新增 `platform-core` capability 的需求定义（本变更只定义 spec 与任务，不实现代码）。
- 约束：后续所有能力必须基于平台核心库提供的：配置加载、DB session、统一响应、错误码、日志脱敏、`camelCase` 输出等。

## Impact（影响）

- 为后续迁移提供稳定接口与约定；降低模块间耦合。
- 明确“库优先 / CLI 必须 / 先写测试”的工程流程。

## Out of Scope（不做什么）

- 不在本提案中实现任何具体业务（用户/策略/回测/交易/风控）。
- 不决定具体数据库/队列选型的最终形态（只定义抽象与最小实现约束）。

## Dependencies（依赖与并行）

- 该变更建议优先实现；完成后其余 bounded context 可并行迁移。

