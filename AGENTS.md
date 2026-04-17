# AGENTS.md

本文件是当前仓库的根级协作入口。重复的项目背景、公共索引和命令入口已下沉到：

- `docs/guides/ai-collaboration.md`
- `docs/guides/ai-context-index.md`
- `docs/README.md`

## 必读顺序

1. `README.md`
2. `docs/guides/ai-collaboration.md`
3. `docs/guides/ai-context-index.md`
4. `openspec/AGENTS.md`（涉及计划 / 提案 / 规格 / 变更时）
5. 当前工作目录下的 `AGENTS.md` 或 `CLAUDE.md`
6. 实际代码与测试

发生冲突时，以当前事实文档、对应目录说明和代码为准。`docs/plans/` 默认不代表当前实现事实。

## 根级硬约束

- 默认使用中文交流与回复；文档输出使用中文 Markdown。
- 落地实现、测试、建模与 UI 约束优先看 `spec/`。
- 本仓库本地版本控制使用 `jj`。
- 执行 OpenSpec CLI 时优先使用 `scripts/openspecw.sh`。
- 用户认证、会话签发、权限判断等用户系统主逻辑必须留在后端，前端只作为 UI 与 API 调用方。

## 项目级 Agent / Skill 入口

- 项目级 agent 规则：`.agent/rules/`
- 项目级私有 skills：`.agents/skills/`
- Codex 可发现的项目级 skills：`skills/`
- 当前项目内 skills：`skills/coolify-fullstack-cutover`、`skills/onevcat-jj`

Skill 约定和多 Agent 约束详见：`docs/guides/ai-collaboration.md`

## 子目录入口

- `apps/backend_app/AGENTS.md`
- `apps/frontend_web/AGENTS.md`
- `deploy/AGENTS.md`
- `docs/frontend/AGENTS.md`
- `libs/frontend_api_client/AGENTS.md`
- `libs/ui_app_shell/AGENTS.md`
- `libs/ui_design_system/AGENTS.md`

## 共享索引

- `docs/guides/ai-collaboration.md`
- `docs/guides/ai-context-index.md`
- `docs/README.md`
- `openspec/AGENTS.md`

## 重要直达索引

- 当前实现事实：`docs/migration/2026-02-13-backend-current-state.md`
- 开发与测试规范：`spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`
- 浏览器测试与 UI 规范：`spec/BrowserTestStrategy.md`、`spec/UISpec.md`、`spec/FrontendArchitectureSpec.md`、`spec/DesignTokensSpec.md`
- 门禁与运行手册：`docs/gates/backend-gate-handbook.md`、`docs/runbooks/backend-operations-runbook.md`
- 后端入口与脚本：`apps/backend_app/`、`scripts/run_backend_server.py`、`scripts/smoke_backend_composition.py`
