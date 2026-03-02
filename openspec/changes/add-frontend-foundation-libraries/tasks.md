## 1. Frontend API Client（ACL）

- [ ] 1.1 设计并固化 `AppError` 结构（kind/code/message/http_status/request_id 可选）
- [ ] 1.2 实现 `request()`：支持 baseUrl + `credentials: 'include'` + 超时 + JSON/文本响应
- [ ] 1.3 实现后端 envelope 解包：`success_response/error_response`
- [ ] 1.4 统一分页结构适配：`page/pageSize/total/items`
- [ ] 1.5 提供最小 endpoints 封装（Auth / Me / Preferences / Health）作为样例
- [ ] 1.6 提供 CLI：输入 `backend_origin`，输出 `health` 与 `cors` 探测结果（JSON）
- [ ] 1.7 单元测试（Vitest 或等价）：错误映射、超时、401 处理

## 2. UI Design System（Base UI + Tailwind v4）

- [ ] 2.1 建立 `cn()`（clsx）与基础样式约定（focus ring、disabled opacity）
- [ ] 2.2 实现基础组件（最小闭环）：
  - [ ] Button（default/hover/focus/disabled/loading）
  - [ ] TextField/Input（label、error、help、disabled）
  - [ ] Select（Base UI）
  - [ ] Dialog/Modal（Base UI）
  - [ ] Toast（可先用最小实现，后续替换）
  - [ ] Table（可组合式）
  - [ ] Skeleton/Spinner/EmptyState
- [ ] 2.3 组件全部从 tokens 取色与间距（禁止 hex 硬编码）
- [ ] 2.4 提供 tokens 校验 CLI：输出 tokens 列表（JSON）并对缺失项返回非 0 exit code
- [ ] 2.5 单元测试：可访问性（tab/focus）、error 状态渲染

## 3. App Shell（布局 + 守卫）

- [ ] 3.1 实现 `PublicLayout` 与 `AppShell`（侧栏 IA 对齐 `spec/UISpec.md`）
- [ ] 3.2 实现 `AuthGuard`：
  - [ ] 进入受保护路由前拉取 `GET /users/me`
  - [ ] 401 统一跳转 `/auth/login?next=...`
- [ ] 3.3 全局错误边界（route-level + app-level）
- [ ] 3.4 全局 Toast 容器与错误上报钩子（可先 stdout/log）

## 4. 工程化与验证

- [ ] 4.1 修改 `apps/frontend_web/app.config.ts` 允许导入 `../../libs/*` 源码（Vite fs allow）
- [ ] 4.2 修改 `apps/frontend_web/tsconfig.json` 增加 path alias（如 `@qp/*`）
- [ ] 4.3 回归验证：
  - [ ] `cd apps/frontend_web && npm run build`
  - [ ] `pytest -q`

