## Why

`update-strategy-research-optimization-depth` 已补齐输入 schema 与读模型，但优化过程仍以规则建议为主。
源需求文档明确要求“网格搜索 + 贝叶斯优化”，当前尚未形成可复算的优化引擎。

## What Changes

- 新增优化方法参数：`grid`、`bayesian`。
- 增加优化 trial 记录与最优解输出模型（含目标函数值、参数组合、约束满足情况）。
- 引入预算边界（最大 trial 数、时间预算、早停条件）。
- 优化结果读模型支持方法维度过滤与版本追踪。

## Impact

- 影响 capability：`strategy-management`
- 关联 capability：`market-data`、`job-orchestration`
- 风险：计算成本上升，需要明确资源与超时治理
