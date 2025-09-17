## 1. Risk 持久化适配器

- [x] 1.1 新增 risk sqlite repository（规则/告警/快照）
- [x] 1.2 接入组合入口并支持 schema 初始化
- [x] 1.3 增加仓储与服务回归测试

## 2. Signal 持久化适配器

- [x] 2.1 新增 signal sqlite repository（信号/执行记录）
- [x] 2.2 接入组合入口并支持 schema 初始化
- [x] 2.3 增加仓储与服务回归测试

## 3. 验证

- [x] 3.1 覆盖重启后数据可恢复场景
- [x] 3.2 保证越权访问语义不变
- [x] 3.3 运行 `openspec validate update-risk-signal-persistence-adapters --strict`
