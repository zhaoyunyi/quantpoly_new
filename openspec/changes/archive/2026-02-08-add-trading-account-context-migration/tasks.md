## 1. 领域建模

- [x] 1.1 新建 `libs/trading_account` 并定义账户/持仓/交易/流水聚合
- [x] 1.2 为每个聚合补充仓储接口与 in-memory 测试实现
- [x] 1.3 提供 CLI：账户查询、持仓分析、交易统计

## 2. API 与所有权

- [x] 2.1 增加账户与持仓相关 API 路由
- [x] 2.2 所有 repository/service 方法显式接收 `user_id`
- [x] 2.3 覆盖越权访问 403 的端到端测试

## 3. 验证

- [x] 3.1 统一响应 envelope 与字段命名
- [x] 3.2 运行 `pytest -q` 与 `openspec validate add-trading-account-context-migration --strict`

