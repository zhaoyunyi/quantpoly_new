## 1. 成功 envelope 规范化

- [x] 1.1 Red：组合入口内部接口成功响应包含标准字段
- [x] 1.2 Red：user-auth 关键成功接口使用统一构造器
- [x] 1.3 Green：替换手写成功响应为 `success_response/paged_response`

## 2. 回归与规范校验

- [x] 2.1 运行 `.venv/bin/pytest -q`
- [x] 2.2 运行 `openspec validate refactor-api-success-envelope-unification --strict`
