# QuantPoly

[![Verify Coolify Local Stack](https://github.com/zhaoyunyi/quantpoly_new/actions/workflows/verify-coolify-local-stack.yml/badge.svg)](https://github.com/zhaoyunyi/quantpoly_new/actions/workflows/verify-coolify-local-stack.yml)

QuantPoly 是一个量化交易平台仓库，当前同时包含后端组合入口、按限界上下文拆分的领域库、Web 前端、部署资产与 OpenSpec 规格。

## 当前状态

- 后端组合入口位于 `apps/backend_app/`，默认运行时存储基线为 `postgres`，本地/测试允许 `memory`。
- 前端应用位于 `apps/frontend_web/`，页面与前端基础库已经落位，`npm ci`、`npm run build`、`npm test` 当前均已恢复通过。
- `2026-04-18` 的一致性审计与收敛记录见 `docs/migration/2026-04-18-doc-code-consistency-audit.md`。

## 仓库结构

- `apps/backend_app/`：FastAPI 组合入口，只负责装配与接线
- `apps/frontend_web/`：TanStack Start Web 前端
- `libs/`：后端领域库、前端 API Client、UI App Shell、UI Design System
- `docs/`：当前事实文档、运行手册、门禁与协作索引
- `openspec/`：当前规格与变更提案
- `spec/`：工程、DDD、BDD、UI 与测试策略约束
- `deploy/`：Coolify 部署模板、本地密钥约定

## 快速入口

### 后端

```bash
uvicorn apps.backend_app:create_app --factory --reload --port 8000
./.venv/bin/python -m apps.backend_app.cli resolve-settings --help
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

### 前端

```bash
cd apps/frontend_web && npm run dev
cd apps/frontend_web && npm run build
cd apps/frontend_web && npm test
```

说明：

- 前端命令入口以上述脚本为准。
- 前端当前包管理基线为 npm；锁文件使用 `package-lock.json`。

## 文档入口

- 当前事实入口：`docs/README.md`
- AI 协作入口：`docs/guides/ai-collaboration.md`
- AI 上下文索引：`docs/guides/ai-context-index.md`
- 后端当前实现事实：`docs/migration/2026-02-13-backend-current-state.md`
- 本次一致性审计与收敛记录：`docs/migration/2026-04-18-doc-code-consistency-audit.md`

## 自动化入口

- 本地一键验证：`./.venv/bin/python scripts/verify_coolify_local_stack.py`
- GitHub Actions 工作流：`.github/workflows/verify-coolify-local-stack.yml`

## 版本控制

本仓库本地版本控制使用 `jj`（Jujutsu）。涉及本地提交、查看状态、整理历史时，应优先使用 `jj` 命令而不是 `git`。
