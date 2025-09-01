## 1. 需求与合同（Spec）

- [ ] 1.1 增加 `signal-execution` 策略驱动生成需求 delta（含场景）
- [ ] 1.2 增加 API 合同测试：`generate-by-strategy` 成功/跳过/越权
- [ ] 1.3 增加 CLI 合同测试：策略驱动生成输出 JSON

## 2. 服务实现（ACL/OHS）

- [ ] 2.1 为 `SignalExecutionService` 增加 `strategy_reader` 与 `market_history_reader` 依赖注入
- [ ] 2.2 实现模板到指标/信号的最小映射（先覆盖 moving_average/mean_reversion）
- [ ] 2.3 生成信号时保留可观测字段（reason/triggered_indicator 等最小元数据）
- [ ] 2.4 保持用户所有权校验不被绕过

## 3. API/CLI

- [ ] 3.1 新增 `/signals/generate-by-strategy` 路由
- [ ] 3.2 为 `signal-execution` CLI 增加子命令

## 4. 验证

- [ ] 4.1 运行相关 pytest
- [ ] 4.2 运行 `openspec validate update-signal-execution-strategy-driven-generation --type change --strict`
