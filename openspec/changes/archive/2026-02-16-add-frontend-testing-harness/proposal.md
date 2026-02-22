# Change: 前端测试基建（Vitest + Playwright + Contract）

## Why

前端重构涉及多条关键链路（登录、策略创建、回测提交、交易执行、监控告警）。为了符合仓库 `Test-First` 与 BDD 验收约束，需要先建立可持续的测试基建与最小主链路用例。

## What Changes

- 为 `apps/frontend_web` 引入：
  - 单元/组件测试：Vitest（可配合 Testing Library）
  - E2E：Playwright（覆盖关键用户旅程）
  - Contract tests：校验后端 envelope/错误码/分页字段与前端类型对齐
- 增加 npm scripts 与 CI 入口（如有）

## Impact

- Affected code:
  - `apps/frontend_web/package.json`（scripts/devDeps）
  - `apps/frontend_web/tests/*`（新增）
- Affected specs:
  - `frontend-testing-harness`

