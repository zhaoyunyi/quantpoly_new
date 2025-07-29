## 1. risk-control 库

- [ ] 1.1 新建 `libs/risk_control` 并抽取规则引擎与告警聚合
- [ ] 1.2 风控规则与报警仓储方法统一增加 `user_id` 显式参数
- [ ] 1.3 增加批量确认/解决/统计的权限隔离测试

## 2. signal-execution 库

- [ ] 2.1 新建 `libs/signal_execution` 并抽取信号与执行记录模型
- [ ] 2.2 修复批量执行/搜索/清理等端点的所有权约束
- [ ] 2.3 对执行趋势、清理接口增加用户范围限制

## 3. 集成与验证

- [ ] 3.1 与 `trading-account`、`strategy-management` 通过 ACL/服务接口解耦
- [ ] 3.2 补充越权回归测试集
- [ ] 3.3 运行 `pytest -q` 与 `openspec validate add-risk-signal-context-migration --strict`

