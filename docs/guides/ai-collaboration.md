# AI 协作入口手册

本文是根 `AGENTS.md` 与 `CLAUDE.md` 共用的仓库级协作入口，用于承接重复的项目背景、执行约定与查阅路径。

## 1. 必读顺序

建议按以下顺序建立上下文：

1. `README.md`
2. `docs/README.md`
3. `spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`、`spec/BrowserTestStrategy.md`、`spec/UISpec.md`、`spec/FrontendArchitectureSpec.md`、`spec/DesignTokensSpec.md`
4. `openspec/specs/` 与 `openspec/changes/`
5. 当前工作目录下的 `AGENTS.md` / `CLAUDE.md`
6. 实际代码与测试

如果文档之间冲突，以当前事实文档、对应目录说明和实际代码为准。`docs/plans/` 默认不代表当前实现事实。

## 2. 仓库硬约束

- 默认使用中文交流与回复；文档输出使用中文 Markdown。
- 开发原则遵循 `spec/ProgramSpec.md`。
- 领域建模遵循 `spec/DDDSpec.md`。
- BDD 场景表达与输出约束遵循 `spec/BDD_TestSpec.md`。
- 浏览器测试选型与边界遵循 `spec/BrowserTestStrategy.md`。
- 前端 UI、架构分层与 Design Tokens 约束分别遵循 `spec/UISpec.md`、`spec/FrontendArchitectureSpec.md`、`spec/DesignTokensSpec.md`。
- 用户认证、会话签发、权限判断等用户系统主逻辑必须留在后端，前端只作为 UI 与 API 调用方。

## 3. 仓库级执行约定

- 涉及计划、提案、规格、变更时，先阅读 `openspec/AGENTS.md`。
- 当前事实优先看 `README.md`、`docs/README.md`、`docs/migration/2026-02-13-backend-current-state.md`、`openspec/specs/`。
- 开发中变更优先看 `openspec/changes/`。
- 本仓库本地版本控制使用 `jj`。
- 执行 OpenSpec CLI 时优先使用 `scripts/openspecw.sh`。
- 落地实现、测试、建模与 UI 约束优先看 `spec/` 目录。

## 4. 项目级 Agent / Skill 入口

- 项目级 agent 规则：`.agent/rules/`
- 项目级私有 skills：`.agents/skills/`
- Codex 可发现的项目级 skills：`skills/`
- 当前项目内 skills 入口：`skills/coolify-fullstack-cutover`、`skills/onevcat-jj`

### Skill 约定

- 与当前项目高度相关、明显依赖仓库目录结构、脚本、部署或运行事实的 skill，优先放到仓库内 `skills/`。
- 只有跨项目复用、与当前仓库弱耦合的通用 skill，才优先放到个人目录（例如 `~/.agents/skills`）。
- 新增或迁移项目内 skill 时，应优先复用并引用现有 `docs/`、`deploy/`、`scripts/`、`spec/` 资产。

## 5. 多 Agent 约束

- 默认不要显式设置 `model` 和 `reasoning_effort`，让子 agent 继承当前主会话配置。
- 如果确实需要显式设置，只允许使用当前主会话同级或更高配置。
- 禁止为 reviewer、spec reviewer、code quality reviewer、explorer、worker 或其他子 agent 自行降级模型或推理强度，除非用户明确同意。
- 调用 `spawn_agent` 前，应先说明子 agent 是否继承主会话模型；如果没有继承，必须说明原因。

## 6. 常用命令入口

### 后端

```bash
uvicorn apps.backend_app:create_app --factory --reload --port 8000
./.venv/bin/python -m apps.backend_app.cli resolve-settings --help
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

### 测试与门禁

```bash
./.venv/bin/pytest
./.venv/bin/pytest -m integration
cat docs/gates/examples/capability_gate_input.json | ./.venv/bin/platform-core capability-gate
./.venv/bin/platform-core storage-contract-gate
```

### 前端

```bash
cd apps/frontend_web && npm run dev
cd apps/frontend_web && npm run build
cd apps/frontend_web && npm run start
cd apps/frontend_web && npm run test
cd apps/frontend_web && npm run test:e2e
```

### OpenSpec

```bash
scripts/openspecw.sh list
scripts/openspecw.sh validate --specs --strict
```

## 7. 目录入口

- 根级事实入口：`README.md`、`docs/README.md`
- 规格与约束入口：`spec/`、`openspec/AGENTS.md`
- 后端组合入口：`apps/backend_app/AGENTS.md`
- 前端入口：`docs/frontend/AGENTS.md`、`apps/frontend_web/AGENTS.md`
- 前端基础库入口：`libs/frontend_api_client/AGENTS.md`、`libs/ui_app_shell/AGENTS.md`、`libs/ui_design_system/AGENTS.md`
- 部署入口：`deploy/AGENTS.md`
- 运行手册与门禁入口：`docs/runbooks/`、`docs/gates/`
- 领域上下文地图：`docs/guides/ai-context-index.md`
