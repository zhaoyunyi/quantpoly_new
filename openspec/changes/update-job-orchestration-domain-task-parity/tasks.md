## 1. 任务类型与编排契约扩展

- [x] 1.1 扩展任务类型（backtest/signal/risk/trading）
- [x] 1.2 定义统一 payload 与结果契约
- [x] 1.3 统一冲突/越权/非法迁移错误码

## 2. 领域接入

- [x] 2.1 回测任务接入编排并返回 taskId
- [x] 2.2 信号批处理接入编排并返回 taskId
- [x] 2.3 风控巡检与交易运维任务接入编排

## 3. 观测与测试

- [x] 3.1 增加任务状态轮询与幂等回归测试
- [x] 3.2 增加任务取消/重试一致性测试
- [x] 3.3 运行 `openspec validate update-job-orchestration-domain-task-parity --strict`
