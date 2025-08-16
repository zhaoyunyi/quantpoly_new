## 1. 判权策略收口

- [x] 1.1 新增统一管理员判定 helper（role/level/is_admin 兼容）
- [x] 1.2 业务路由删除裸字段判定，统一走 helper
- [x] 1.3 判权失败与越权错误码语义统一

## 2. 治理审计补齐

- [x] 2.1 高风险动作审计记录补充判权来源字段
- [x] 2.2 token/cookie/password 字段脱敏校验补齐

## 3. 测试与校验

- [x] 3.1 增加 admin/user 两类身份回归用例
- [x] 3.2 增加迁移兼容输入（仅 `is_admin`）用例
- [x] 3.3 运行 `openspec validate update-admin-role-resolution-parity --strict`
