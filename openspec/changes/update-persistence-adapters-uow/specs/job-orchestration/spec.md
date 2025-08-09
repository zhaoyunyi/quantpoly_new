## ADDED Requirements

### Requirement: 任务编排必须依赖持久化队列状态与唯一约束
任务提交、查询、状态迁移 MUST 基于持久化状态存储，并对 `idempotencyKey` 强制唯一约束。

#### Scenario: 并发提交任务时保持唯一与一致
- **GIVEN** 同一用户并发提交携带相同 `idempotencyKey` 的任务
- **WHEN** 系统执行任务入队
- **THEN** 仅允许一个任务创建成功
- **AND** 其余请求必须返回明确幂等冲突语义
