## 1. 优化引擎模型

- [x] 1.1 定义 grid/bayesian 方法与配置 schema
- [x] 1.2 定义 trial/score/best-candidate 读模型
- [x] 1.3 定义预算约束（trials/time/early-stop）

## 2. 任务与查询

- [x] 2.1 研究任务支持 method 与 budget 入参
- [x] 2.2 结果持久化保存 trial 明细与最优解
- [x] 2.3 查询接口支持按 method/status/version 过滤

## 3. CLI 与可观测

- [x] 3.1 CLI 支持 method 与 budget 参数
- [x] 3.2 输出优化过程摘要（trial count/耗时/收敛状态）
- [x] 3.3 补充 break update 迁移说明

## 4. 测试与验证

- [x] 4.1 Red：grid 与 bayesian 基础路径
- [x] 4.2 覆盖预算限制、早停、失败恢复
- [x] 4.3 运行 `openspec validate update-strategy-optimization-engine-grid-bayes --strict`
