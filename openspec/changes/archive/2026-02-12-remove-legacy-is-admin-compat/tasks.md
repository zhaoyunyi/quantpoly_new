## 1. 统一管理员判定来源

- [x] 1.1 Red：legacy is_admin 不再被识别为管理员
- [x] 1.2 Green：authz 仅基于 role/level 判定

## 2. API 行为一致性

- [x] 2.1 trading-account：legacy is_admin 访问 ops 接口返回 403/ADMIN_REQUIRED
- [x] 2.2 signal-execution：legacy is_admin 访问全局维护接口返回 403/ADMIN_REQUIRED

## 3. 回归与规范验证

- [x] 3.1 回归 platform-core/trading-account/signal-execution 测试
- [x] 3.2 运行 `openspec validate remove-legacy-is-admin-compat --strict`
