## 1. 监控读模型设计

- [x] 1.1 定义运营摘要字段（accounts/strategies/backtests/tasks/signals/alerts）
- [x] 1.2 定义跨上下文读接口（ACL/OHS）并落实 ownership 过滤
- [x] 1.3 约定字段语义与版本化策略

## 2. API 与 WS 语义统一

- [x] 2.1 改造 `/monitor/summary` 输出为运营读模型
- [x] 2.2 对齐 WS 推送中计数字段与摘要语义
- [x] 2.3 增加降级字段与空数据语义

## 3. 可观测与文档

- [x] 3.1 增加摘要生成耗时与数据来源标记
- [x] 3.2 更新监控域 API/字段说明
- [x] 3.3 输出 break update 迁移说明

## 4. 测试与验证

- [x] 4.1 先写失败测试（Red）：任务计数、跨域一致性、越权过滤
- [x] 4.2 完成 API + WS 一致性回归测试
- [x] 4.3 运行 `openspec validate update-monitoring-summary-operational-parity --strict`
