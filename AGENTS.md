<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

# 协作约定（必读）

- 默认使用中文交流与回复；文档输出使用中文 Markdown。
- 当请求涉及“计划/提案/规格/变更”（proposal/spec/change/plan 等）时，先阅读 `openspec/AGENTS.md` 再开始编码。

## Superpowers（技能系统）

Superpowers 已通过 Codex 原生 skill discovery 安装，无需再使用旧版 `superpowers-codex bootstrap`。

- Superpowers 仓库：`~/.codex/superpowers`
- Skills 入口（symlink）：`~/.agents/skills/superpowers` → `~/.codex/superpowers/skills`
- 若某次会话中技能未出现：先确认上述 symlink 存在，再重启 Codex CLI

---

# 项目结构速览

- `apps/`：应用层
  - `apps/backend_app/`：后端组合入口（FastAPI Composition Root）
  - `apps/frontend_web/`：前端 Web（TanStack Start + Tailwind CSS v4）
- `libs/`：领域/平台库（多数为独立 Python 包；部分为占位或未打包库）
- `tests/`：仓库级测试（可直接在仓库根目录运行 `pytest`）
- `spec/`：实现/测试/建模规范（落地约束，以此为准）
- `openspec/`：OpenSpec 工作流（变更提案、能力 specs）
- `docs/`：与当前实现一致的文档入口/运行手册/门禁手册
- `scripts/`：冒烟与运维脚本

---

# 规范与文档索引（先读再改）

除上述 OpenSpec 工作流外，本仓库还在 `spec/` 目录维护了更偏“落地实现/测试/建模”的规范。进行任何实现、测试、命名建模相关的工作前，请先阅读并遵守：

- `spec/ProgramSpec.md`：Specify Protocol（核心开发三原则）
  - **Library-First**：任何功能必须先抽为可复用的独立库
  - **CLI Mandate**：每个库必须提供 CLI（stdin/args/files 输入，stdout 输出，支持 JSON）
  - **Test-First**：严格 TDD；先写并确认失败的测试（Red）再写实现
- `spec/DDDSpec.md`：DDD 核心原则（通用语言 / 限界上下文 / 聚合与充血模型）
- `spec/BDD_TestSpec.md`：BDD 测试与输出格式规范（Given/When/Then；snake_case 分层日志输出）
- `spec/UISpec.md`：UI 规范（前端视觉与交互基线）
- `spec/FrontendArchitectureSpec.md`：前端架构分层与边界
- `spec/DesignTokensSpec.md`：Design Tokens 命名与输出约束

与“当前实现事实”保持一致的文档入口：

- `docs/README.md`：文档总入口（只保留与当前代码实现一致的文档）
- `docs/migration/2026-02-13-backend-current-state.md`：后端当前实现状态（实现事实）
- `docs/runbooks/backend-operations-runbook.md`：后端发布/切换/冒烟/观测基线
- `docs/gates/backend-gate-handbook.md`：门禁手册
- `docs/frontend/AGENTS.md`：前端建设文档入口（规范与目录约定）

前端子项目约定：

- `apps/frontend_web/AGENTS.md`

---

# 常用命令

## Python 测试

- 单元测试（默认跳过集成测试）：`./.venv/bin/pytest`（配置见 `pytest.ini`；若未使用仓库自带 `.venv/`，则用 `pytest`）
- 运行集成测试：`./.venv/bin/pytest -m integration`（或 `pytest -m integration`）
  - 集成测试依赖 Postgres：`docker compose up -d postgres`（见 `docker-compose.yml`，对外端口 `54329`）

## 后端（组合入口/冒烟/门禁）

- 本地启动（需要环境中已安装 `uvicorn`）：`uvicorn apps.backend_app:create_app --factory --reload --port 8000`
- 组合配置解析 CLI：`./.venv/bin/python -m apps.backend_app.cli resolve-settings --help`
- 切换前冒烟：`python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000`
- 能力门禁：`cat docs/gates/examples/capability_gate_input.json | ./.venv/bin/platform-core capability-gate`
- 存储契约防回流门禁：`./.venv/bin/platform-core storage-contract-gate`

## 前端（TanStack Start）

- 开发启动：`cd apps/frontend_web && npm run dev`
- 生产构建：`cd apps/frontend_web && npm run build`
- 本地预览：`cd apps/frontend_web && npm run start`

---

# Git 提交规范（必须使用 git cnd）

本仓库的“提交日期策略”依赖本地 Git alias：`git cnd`。

- **请使用 `git cnd` 提交**，不要直接用 `git commit`（否则不会自动设置提交日期）。
- 规则摘要：
  - 距离上一次 `git cnd` 的真实执行时间 **< 5 分钟**：视为同一天（日期不变）
  - 距离上一次 `git cnd` 的真实执行时间 **≥ 5 分钟**：日期在上次基础上 **+1 天**
  - 提交时间默认使用**当前系统时间（时分秒）**，也可用 `--time HH:MM:SS` 覆盖
- 首次提交（仓库无 commit）示例：`git cnd --start-date 2025-07-17 -m "chore: init"`
- 检查 alias 是否已安装：`git config --local --get alias.cnd`
- 5 分钟规则的状态（epoch 秒）存放在：`cnd.last-epoch`
  - 查看：`git config --local --get cnd.last-epoch`
  - 重置：`git config --local --unset cnd.last-epoch`
