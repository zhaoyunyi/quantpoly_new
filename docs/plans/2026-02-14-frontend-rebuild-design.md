# QuantPoly 前端重构设计（TanStack Start + Base UI + Tailwind）

**目标**：在本仓库内补齐前端项目（`apps/frontend_web`），并在不破坏现有后端代码/脚本可用性的前提下，使用 **TanStack Start + Base UI + Tailwind v4** 重新实现旧项目前端的全部核心路由与功能（1:1 覆盖）。

**范围基线**（旧前端路由集）：
- Landing：`/`
- Auth：`/auth/login`、`/auth/register`、`/auth/forgot-password`、`/auth/reset-password`、`/auth/verify-email`、`/auth/resend-verification`
- Dashboard：`/dashboard`
- Strategies：`/strategies`、`/strategies/$id`、`/strategies/simple`、`/strategies/advanced`、`/strategies/compare`
- Backtests：`/backtests`、`/backtests/$id`
- Trading：`/trading`、`/trading/accounts`、`/trading/analytics`
- Monitor：`/monitor`
- Settings：`/settings`、`/settings/theme`、`/settings/account`

---

## 1. 运行拓扑与会话/鉴权（HTTP 直连后端 + CORS）

### 1.1 Origin 约定

前端与后端为不同 Origin（端口不同也算不同 Origin），但**建议同域同 scheme**（例如都用 `http://localhost`），以满足 cookie 的 `SameSite=Lax` 行为。

- `FRONTEND_ORIGIN`（示例）：`http://localhost:3300`
- `BACKEND_ORIGIN`（示例）：`http://localhost:8000`

> 禁止混用 `localhost` 与 `127.0.0.1`，否则 cookie/WS 鉴权会出现“看似登录成功但请求不带 cookie”的问题。

### 1.2 HTTP API 调用策略

- 浏览器端 **HTTP 直连后端**（不经过前端代理）：前端所有 `fetch` 必须使用 `credentials: 'include'` 以携带 `session_token` cookie。
- 后端必须开启 CORS，并满足：
  - `Access-Control-Allow-Origin` 精确匹配前端 origin（**禁止 `*`**）
  - `Access-Control-Allow-Credentials: true`
  - 允许方法：`GET/POST/PUT/PATCH/DELETE/OPTIONS`
  - 允许头：`Content-Type/Authorization/...`（至少覆盖实际请求）

### 1.3 WebSocket 策略（直连后端）

前端直接连接后端 WebSocket（不做代理/bridge）：
- 监控：`ws(s)://<BACKEND_ORIGIN>/ws/monitor`
- 行情流：`ws(s)://<BACKEND_ORIGIN>/market/stream`

鉴权约束：
- 后端 WS 鉴权只接受 `Cookie session_token` 或 `Authorization: Bearer <token>`
- 浏览器原生 `WebSocket` 无法自定义 `Authorization` header，因此**WS 必须依赖 cookie**，这要求前后端保持 same-site（同域同 scheme）。

---

## 2. 路由信息架构与模块边界

### 2.1 路由结构（TanStack Router file routes）

保持与旧前端路径尽量一致（便于迁移与 E2E 对照）。页面分两类：
- Public（不要求登录）：Landing、Auth
- Auth Required（要求登录）：Dashboard/Strategies/Backtests/Trading/Monitor/Settings

### 2.2 布局与路由守卫

- `PublicLayout`：登录/注册/找回等页面统一壳
- `AppShell`：侧栏一级导航 + 顶部工具条 + 内容区
- 守卫策略：进入受保护路由前，拉取 `GET /users/me` 决定放行；401 统一跳转 `/auth/login?next=...`

### 2.3 前端分层（遵循 `spec/FrontendArchitectureSpec.md`）

前端代码按职责分层（同一层只做同一类事情）：
- `pages`：路由页面编排
- `widgets`：页面级复合组件（可跨 features）
- `features`：领域交互逻辑（表单、提交、状态机、批量操作）
- `entities`：领域实体展示与轻量本地行为（只展示，不做复杂 orchestration）
- `shared`：通用工具（格式化、错误模型、鉴权态、UI 原子组件）

跨上下文交互通过 ACL：
- 任何后端调用只允许通过 `frontend_api_client`（错误映射、分页、envelope 解包、重试策略）

---

## 3. 数据层、错误模型、缓存与 WS 订阅模型

### 3.1 统一响应 Envelope

后端主要遵循 `platform_core.success_response/error_response`，前端必须统一解包并映射为稳定错误模型：
- `AppError.kind`：`network` | `auth` | `validation` | `conflict` | `unknown`
- `AppError.code`：后端 `error.code`
- `AppError.message`：用户可读（可二次映射）
- `AppError.httpStatus`

### 3.2 状态管理约束

- **服务端状态**（列表/详情/统计/任务状态）只允许进入 TanStack Query 缓存
- **UI 状态**（筛选器、drawer、选中项、表格列配置）允许放轻量 store 或 URL search params
- 禁止在 store 中缓存服务端列表数据，避免与 Query 语义打架

### 3.3 WebSocket 协议对接

- `/ws/monitor`：
  - 连接后发送 `subscribe`（channels: `signals/alerts`）
  - 支持 `ping/pong`、`poll`（增量）、`resync`（全量）
  - 消息类型覆盖：`monitor.heartbeat`、`signals_update`、`risk_alert`
- `/market/stream`：
  - 消息动词为 `action`：`subscribe/unsubscribe/status`
  - 事件：`stream.ready`、`stream.subscribed`、`market.quote`、`stream.degraded`
  - 收到 `stream.degraded` 时自动降级为 HTTP 轮询 `/market/quote/{symbol}` 或 `/market/quotes`

---

## 4. 对齐矩阵：旧前端功能点 -> 当前后端端点

> 说明：该表用于实现拆分与验收，不代表最终 UI 形态。

| 前端路由 | 关键功能点 | 后端端点（当前仓库） |
| --- | --- | --- |
| `/auth/register` | 注册 | `POST /auth/register` |
| `/auth/login` | 登录（cookie session） | `POST /auth/login`、`GET /users/me` |
| `/auth/logout` | 登出 | `POST /auth/logout` |
| `/auth/verify-email` | 邮箱验证（当前后端为按 email 验证） | `POST /auth/verify-email` |
| `/auth/resend-verification` | 重发验证邮件 | **后端需补充**（建议新增 `POST /auth/verify-email/resend` 或等价） |
| `/auth/forgot-password` | 发起找回 | `POST /auth/password-reset/request` |
| `/auth/reset-password` | 确认找回 | `POST /auth/password-reset/confirm` |
| `/dashboard` | 总览卡片 | `GET /monitor/summary`、`GET /trading/accounts/aggregate`、`GET /backtests/statistics`、`GET /risk/alerts/stats`（可选） |
| `/strategies` | 列表/搜索/筛选/创建/删除/激活等 | `GET/POST /strategies`、`GET/PUT/DELETE /strategies/{id}`、`POST /strategies/{id}/activate`、`POST /strategies/{id}/deactivate`、`POST /strategies/from-template`、`GET /strategies/templates` |
| `/strategies/$id` | 详情、编辑、关联回测 | `GET /strategies/{id}`、`PUT /strategies/{id}`、`GET /strategies/{id}/backtests`、`GET /strategies/{id}/backtest-stats` |
| `/strategies/simple` | 向导创建 + 可选一键回测 | `GET /strategies/templates`、`POST /strategies/from-template`、`POST /strategies/{id}/backtests` 或 `POST /backtests` |
| `/strategies/compare` | 多策略对比 | `POST /backtests/compare`（按回测 taskIds）；或新增后端 read model（可选） |
| `/backtests` | 列表、统计、提交任务、取消/重试、重命名 | `GET/POST /backtests`、`POST /backtests/tasks`、`GET /backtests/statistics`、`POST /backtests/{id}/cancel`、`POST /backtests/{id}/retry`、`PATCH /backtests/{id}/name` |
| `/backtests/$id` | 详情、结果、相关回测 | `GET /backtests/{id}`、`GET /backtests/{id}/result`、`GET /backtests/{id}/related` |
| `/trading` | 交易主控（账户概览/持仓/下单） | `GET /trading/accounts`、`GET /trading/accounts/{id}/summary`、`GET /trading/accounts/{id}/positions`、`POST /trading/accounts/{id}/buy`、`POST /trading/accounts/{id}/sell`、`GET/POST /trading/accounts/{id}/orders` |
| `/trading/accounts` | 账户管理 | `GET/POST /trading/accounts`、`GET /trading/accounts/filter-config`、`PUT /trading/accounts/{id}` |
| `/trading/analytics` | 分析（风险/绩效/曲线/流水） | `GET /trading/accounts/{id}/risk-metrics`、`GET /trading/accounts/{id}/equity-curve`、`GET /trading/accounts/{id}/cash-flows`、`GET /trading/accounts/{id}/trade-stats` |
| `/monitor` | 实时监控（signals/alerts） | `GET /monitor/summary`、`WS /ws/monitor`、并联 `GET /signals/*`、`GET /risk/alerts*` |
| `/settings` | 偏好总览 | `GET/PATCH /users/me/preferences`、`GET/PATCH /users/me` |
| `/settings/theme` | 主题偏好 | `PATCH /users/me/preferences`（theme 子树） |
| `/settings/account` | 账号资料/密码/注销 | `PATCH /users/me`、`PATCH /users/me/password`、`DELETE /users/me` |
| `/` | Landing | 可选 `GET /health` 做运行状态提示 |

---

## 5. 测试策略（TDD + BDD 表达）

分三层覆盖主链路：
1. 单元测试（Vitest）：工具函数、错误映射、API client、关键组件状态机
2. 集成测试（Vitest + MSW 或 fetch mock）：页面流程与接口交互（不依赖真实后端）
3. E2E（Playwright）：覆盖登录 -> 策略创建 -> 回测提交 -> 交易下单（模拟） -> 告警处理 的端到端流程

并补充合约测试（Contract Tests）：
- 校验关键接口的 envelope、错误码、分页字段与前端类型一致

> 输出规范：若以“BDD 报告”形式输出结果，需遵循 `spec/BDD_TestSpec.md` 的 snake_case 分层输出约束。

---

## 6. OpenSpec 并行拆分（建议 Change 列表）

建议将前端重构拆为可并行评审/实现的多个 Change（存在依赖的标注为 prerequisite）：

1. `add-backend-cors-for-frontend-web`（prerequisite：HTTP 直连后端）
2. `add-frontend-foundation-libraries`（prerequisite：各页面实现）
3. `add-frontend-auth-pages`
4. `add-frontend-dashboard-pages`
5. `add-frontend-strategy-management-pages`
6. `add-frontend-backtest-center-pages`
7. `add-frontend-trading-pages`
8. `add-frontend-monitoring-pages`
9. `add-frontend-settings-pages`
10. `add-frontend-landing-page`
11. `add-frontend-testing-harness`

后续独立处理（避免引入破坏性升级影响主线）：
- `update-frontend-security-dependencies`（集中处理 `npm audit` 高危/中危依赖）
