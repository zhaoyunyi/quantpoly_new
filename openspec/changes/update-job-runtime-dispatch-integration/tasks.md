## 1. 运行时与执行器

- [ ] 1.1 定义运行时模式配置与执行器选择策略（inprocess/celery-adapter）
- [ ] 1.2 统一 dispatch callback 的状态变迁与错误码映射
- [ ] 1.3 完善执行器健康与恢复读模型

## 2. 任务派发链路

- [ ] 2.1 业务域任务提交改为真实 dispatch 路径
- [ ] 2.2 移除域 API 内“提交即成功”的同步短路
- [ ] 2.3 保持幂等冲突与权限语义不变

## 3. 调度模板

- [ ] 3.1 增加系统任务调度模板注册机制
- [ ] 3.2 支持调度模板恢复与重复注册防抖
- [ ] 3.3 提供 CLI/API 可观测输出

## 4. 测试与验证

- [ ] 4.1 Red：dispatch 成功/失败/超时与回调语义
- [ ] 4.2 Green：跨域任务 API 状态流一致性
- [ ] 4.3 运行 `openspec validate update-job-runtime-dispatch-integration --strict`
