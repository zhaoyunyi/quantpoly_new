# move-user-preferences-to-backend Tasks

## 1. 规范

- [x] 1.1 创建 capability `user-preferences` spec（`openspec/specs/user-preferences/spec.md`）

## 2. 实现（后续执行阶段）

- [x] 2.1 提供 preferences 默认值与版本迁移器（library + CLI）
- [x] 2.2 实现 preferences API（GET/PATCH/reset/export/import）
- [x] 2.3 增加权限校验：`advanced` 仅高等级用户可见/可写
