## 1. 治理模型与策略

- [ ] 1.1 新建 `libs/admin_governance` 并定义管理员动作模型（action catalog）
- [ ] 1.2 实现统一授权策略引擎（role/level/policy）
- [ ] 1.3 为高风险动作实现二次确认令牌（短 TTL、单次使用）

## 2. 接入与约束

- [ ] 2.1 在维护/清理/批量操作接口接入治理检查器
- [ ] 2.2 普通用户触发全局维护动作统一返回 403
- [ ] 2.3 输出治理审计日志（actor/action/target/result）

## 3. 验证

- [ ] 3.1 增加越权回归测试（普通用户误调用管理员动作）
- [ ] 3.2 增加审计日志脱敏测试（不得泄漏 token/cookie）
- [ ] 3.3 运行 `pytest -q` 与 `openspec validate add-admin-governance-context-migration --strict`

