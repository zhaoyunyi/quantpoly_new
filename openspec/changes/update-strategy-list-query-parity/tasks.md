## 1. 查询模型

- [ ] 1.1 定义策略列表查询参数模型（status/search/page/pageSize）
- [ ] 1.2 定义分页读模型输出（items/total/page/pageSize）

## 2. API 与 CLI

- [ ] 2.1 API `GET /strategies` 支持过滤与分页
- [ ] 2.2 CLI `list` 支持过滤与分页参数

## 3. 测试与验证

- [ ] 3.1 Red：状态筛选、关键词搜索、分页边界
- [ ] 3.2 Green：实现与回归
- [ ] 3.3 运行 `openspec validate update-strategy-list-query-parity --strict`
