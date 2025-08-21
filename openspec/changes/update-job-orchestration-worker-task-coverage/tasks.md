## 1. 任务类型覆盖扩展

- [ ] 1.1 定义 Wave3 任务类型注册表（strategy/signal/risk/trading/market-data）
- [ ] 1.2 统一任务类型校验与错误码语义
- [ ] 1.3 增加任务类型查询能力（API + CLI）

## 2. 调度与治理语义收口

- [ ] 2.1 调度配置引入用户范围/命名空间规则
- [ ] 2.2 补齐调度查询与审计字段
- [ ] 2.3 校验跨租户调度越权拒绝语义

## 3. 测试与验证（TDD）

- [ ] 3.1 先写失败测试：任务类型注册/查询/越权
- [ ] 3.2 最小实现使测试通过并重构
- [ ] 3.3 运行 `openspec validate update-job-orchestration-worker-task-coverage --strict`
