## 1. 读模型设计

- [ ] 1.1 定义执行模板按类型查询读模型
- [ ] 1.2 定义按策略统计与趋势读模型（字段口径固定）
- [ ] 1.3 通过 ACL 读取策略域信息，禁止跨域仓储直连

## 2. API 与 CLI

- [ ] 2.1 增加执行查询 API（路径可 break，语义稳定）
- [ ] 2.2 增加 CLI 查询命令，输出 JSON

## 3. 测试与验收

- [ ] 3.1 先写失败测试（Red）：模板查询、策略统计、趋势查询
- [ ] 3.2 验证越权策略查询返回 403
- [ ] 3.3 运行 `openspec validate update-strategy-execution-query-readmodel --strict`
