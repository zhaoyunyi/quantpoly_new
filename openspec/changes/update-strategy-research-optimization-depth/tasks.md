## 1. 研究领域模型

- [ ] 1.1 定义 ResearchRun/OptimizationResult 聚合与状态机
- [ ] 1.2 定义优化目标与参数搜索空间 schema
- [ ] 1.3 设计结果评分与建议输出结构

## 2. 任务链路与读模型

- [ ] 2.1 研究任务提交支持目标函数与约束输入
- [ ] 2.2 结果持久化并关联 job/taskId
- [ ] 2.3 新增研究结果查询接口（按策略/时间/状态）

## 3. CLI 与可观测

- [ ] 3.1 扩展 strategy-management CLI 的研究任务命令
- [ ] 3.2 增加研究任务耗时与参数回显日志（脱敏）
- [ ] 3.3 产出 break update 迁移说明

## 4. 测试与验证

- [ ] 4.1 先写失败测试（Red）：参数空间校验、结果持久化、读模型查询
- [ ] 4.2 覆盖异步任务完成/失败/取消场景
- [ ] 4.3 运行 `openspec validate update-strategy-research-optimization-depth --strict`
