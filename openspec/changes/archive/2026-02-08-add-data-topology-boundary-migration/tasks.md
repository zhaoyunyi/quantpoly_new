## 1. 边界定义

- [x] 1.1 新建 `libs/data_topology_boundary` 并定义模型归属与存储边界清单
- [x] 1.2 输出跨库访问策略（ACL/Anti-Corruption Layer）
- [x] 1.3 提供 CLI：模型归属校验、跨库引用扫描、迁移 dry-run

## 2. 迁移与一致性

- [x] 2.1 为跨库迁移定义标准脚本模板（up/down + 回填）
- [x] 2.2 定义一致性补偿机制（重试/对账/告警）
- [x] 2.3 为关键模型迁移增加回滚演练测试

## 3. 验证

- [x] 3.1 增加“非法跨库依赖”检测测试
- [x] 3.2 增加迁移前后数据一致性对账测试
- [x] 3.3 运行 `pytest -q` 与 `openspec validate add-data-topology-boundary-migration --strict`

