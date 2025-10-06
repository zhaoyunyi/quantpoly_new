# API 契约治理：响应 Envelope 与路由命名统一（P1 设计稿）

> 日期：2026-02-12
>
> 背景：Wave0~Wave7 的“功能迁移”已完成并归档，进入“治理型重构”阶段。

## 1. 结论（盘点）

- 对照旧项目（`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`）与当前仓库，核心业务能力缺口已清零（详见 `docs/migration/2026-02-12-remaining-backend-migration-audit.md`）。
- 当前主要问题不是“功能缺失”，而是 **API 契约不一致**：
  - 同一能力在**组合入口** vs **standalone app / 测试 app** 的返回结构不同；
  - `user-auth` 的业务错误码在部分路径下会被“吞掉/降级”，与 spec 中“可识别业务错误码”的要求不一致。

## 2. 产品愿景对齐（来自旧项目需求文档）

旧项目愿景与核心路径（摘要自 `docs/需求分析最终版本.md`、`docs/技术架构详细设计文档.md`）：

- 产品定位：个人股票量化策略研究与验证平台
- 核心价值：零编程门槛、专业回测、参数优化、模拟交易、风险可控、实时监控

当前仓库的 bounded contexts（`user-auth / strategy-management / backtest-runner / trading-account / market-data / risk-control / signal-execution / monitoring-realtime / job-orchestration`）已覆盖上述主路径。

因此本轮调整以 **契约治理/可维护性** 为目标，不引入新业务能力。

## 3. 现状问题（证据）

### 3.1 错误响应不一致（standalone vs composition）

- `backend_app` 组合入口安装了 `HTTPException / RequestValidationError / Exception` handler，统一输出 `platform_core.error_response(...)`。
- 但 `user_auth.create_app()` 与部分测试用 `FastAPI()` app **未安装 handler**，导致错误体为 FastAPI 默认 `{"detail": ...}`。
- 同时 `user-auth` 目前存在 `detail="EMAIL_NOT_VERIFIED"` 这类字符串错误码：在组合入口中会被映射为 `error.code=FORBIDDEN`，业务错误码丢失（spec 要求 `EMAIL_NOT_VERIFIED` 这类业务码可识别）。

### 3.2 路由命名存在语义不一致点

- `user-auth` 目前 `GET /auth/me`，而用户资料更新是 `PATCH /users/me`。
- 同一资源（当前用户资料）使用了不同前缀，增加客户端心智负担，也让 docs/spec 难以给出单一权威路径。

## 4. 目标 / 非目标

### 目标

1. **错误 envelope 一致**：所有对外 API（含 standalone/test harness）在发生业务/权限/校验错误时，返回 `success=false` + `error.code/error.message`。
2. **业务错误码保真**：`user-auth` 相关错误码（如 `EMAIL_NOT_VERIFIED`、`USER_DISABLED`、`MISSING_TOKEN`）在任何运行形态下保持一致。
3. **路由语义一致**：统一“用户资源”的路由前缀（`/users/...`），避免 `/auth` 与 `/users` 混用同一资源。

### 非目标

- 不做“所有上下文同时全量重命名”的大爆炸式改造（避免一次性 break 面过大）。
- 不引入新的业务功能或持久化模型变更。

## 5. 方案对比

### 方案 A（最小）：仅在 backend_app 统一异常处理

- 优点：改动小
- 缺点：standalone/test harness 仍不一致；`user-auth` 业务码仍可能丢失
- 结论：不推荐

### 方案 B（推荐）：平台提供可复用异常处理安装器

- 在 `platform_core` 提供 `install_exception_handlers(app)`，将 `HTTPException / RequestValidationError / 未知异常` 统一映射为 `error_response`
- `backend_app` 与各库的 standalone app / 测试 app 显式安装
- `user-auth` 抛出的 `HTTPException` 统一使用 `detail={code,message}`，保证 `error.code` 保真

结论：推荐（契约治理收益最高，且改动可控）

### 方案 C（最大）：同时全量路由重命名 + envelope 统一

- 优点：一次到位
- 缺点：极大 break update；工作量与回归风险高
- 结论：拆分为多个 OpenSpec 逐步推进

## 6. OpenSpec 拆分（按依赖/可并行）

1. `refactor-api-error-envelope-unification`（基座，先做）
2. `refactor-api-success-envelope-unification`（可并行，次优先）
3. `refactor-route-naming-normalization`（最后做，break update 面最大）

依赖图：

```text
refactor-api-error-envelope-unification
    ├── refactor-api-success-envelope-unification
    └── refactor-route-naming-normalization
```

## 7. 测试策略（TDD/BDD）

- 每个变更先写/改测试进入 Red，再实现 Green
- 最小覆盖：
  - `user-auth`：未验证邮箱登录、禁用用户登录、缺 token 访问受保护接口、请求体校验错误（422）
  - `user-preferences`：403/422 在 standalone app 下也输出 error_response（结构一致即可）
- 回归：`.venv/bin/pytest -q`
- 规范：`openspec validate <change-id> --strict`

## 8. 风险与回滚

- **BREAKING**：客户端若依赖 `detail` 字段，需要改为读取 `error.code/error.message`。
- 回滚策略：保持 HTTP status code 不变；若出现客户端阻断，可临时在组合入口提供兼容映射（但应避免长期存在）。

## 9. 下一步

我将先在 `openspec/changes/` 生成上述 3 个提案（proposal/tasks/spec delta），并运行 `openspec validate --strict`。

你确认提案内容后，再进入实现阶段（严格 TDD）。

