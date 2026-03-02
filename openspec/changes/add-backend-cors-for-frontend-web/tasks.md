## 1. Settings & Config

- [ ] 1.1 在 `apps/backend_app/settings.py` 增加 CORS 相关配置读取（允许 origins、是否允许 credentials、允许方法/头）
- [ ] 1.2 定义默认行为：未配置时保持“关闭 CORS”（避免对现有后端脚本产生意外影响）

## 2. Middleware 安装

- [ ] 2.1 在 `apps/backend_app/app.py` 的 `create_app()` 安装 `CORSMiddleware`
- [ ] 2.2 记录安全约束：`Access-Control-Allow-Origin` 必须为显式 origin（禁止 `*`）且允许 credentials

## 3. 测试（TDD）

- [ ] 3.1 新增测试：`OPTIONS` 预检返回包含 `access-control-allow-origin`、`access-control-allow-credentials`
- [ ] 3.2 新增测试：跨域携带 cookie 的请求可访问 `GET /health`（无需认证）并通过 CORS
- [ ] 3.3 新增测试：跨域携带 cookie 的受保护请求（如 `GET /users/me`）在缺少 cookie 时返回 401，并仍带正确 CORS 头（前端可读错误）

## 4. 文档与验证

- [ ] 4.1 在 `docs/plans/` 或相关运行手册补充开发期推荐 origin 约定（统一使用 `localhost`）
- [ ] 4.2 运行回归：`pytest -q`

