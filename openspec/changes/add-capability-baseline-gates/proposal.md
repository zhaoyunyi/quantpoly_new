## Why

在本轮迁移策略中，项目明确采用“允许 breaking change，但功能不能缺失”的硬约束。

当前仓库虽已完成多批后端 context 迁移，但尚缺少统一的“能力等价”验收闸门，导致以下风险：

- 仅凭接口或代码完成度无法判断“用户可用能力是否完整”；
- 波次切换时缺少统一的放行/阻断标准；
- 发生缺陷时缺少清晰回滚判定依据。

## What Changes

- 新增迁移能力基线（Capability Baseline）治理变更：
  - 定义“用户旅程 + 限界上下文能力”双维度能力矩阵；
  - 定义每个 Wave 的切换门禁（通过/阻断）标准；
  - 定义失败回滚触发条件与最小回滚步骤；
  - 将能力门禁纳入 OpenSpec 评审与发布流程。

## Impact

- 影响 capability：`platform-core`
- 被约束 capability：`user-auth`、`user-preferences`、`strategy-management`、`backtest-runner`、`trading-account`、`market-data`、`risk-control`、`signal-execution`、`job-orchestration`、`monitoring-realtime`
