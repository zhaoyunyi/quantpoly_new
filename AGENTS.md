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

## gstack（Claude Code）

- 当前仓库允许在 Claude Code 中按需使用 `gstack` 的 slash workflows。
- 涉及网页浏览、站点验证、截图、交互式 QA 时，优先使用 `/browse`、`/qa`、`/qa-only`、`/open-gstack-browser`。
- 常用流程命令包括：`/office-hours`、`/autoplan`、`/review`、`/investigate`、`/ship`、`/cso`。
- 使用 `gstack` 相关文件路径时，优先使用全局安装路径 `~/.claude/skills/gstack/...`。
- 不使用 `mcp__claude-in-chrome__*` 作为本仓库默认网页浏览方案。

## Skill routing（Claude Code）

适用范围：仅适用于已安装 `gstack` 的 Claude Code 会话。对于 Codex 或其他不支持 `gstack` slash workflows 的宿主，不要求模拟这些命令。

- 当用户请求明显匹配已安装的 `gstack` skill 时，优先先调用对应 skill，不要先直接自由回答，也不要先走其他网页工具。
- 产品想法、是否值得做、头脑风暴、方案方向判断，优先用 `/office-hours`。
- Bug、报错、异常行为、线上故障排查，优先用 `/investigate`。
- 发版、部署、推送、创建 PR，优先用 `/ship`；若已进入部署验证阶段，优先用 `/land-and-deploy`。
- 网页浏览、打开站点、截图、页面交互、人工验收式测试，优先用 `/browse`；如果需要完整可视浏览器，优先用 `/open-gstack-browser`。
- QA、测试站点、找 bug、回归验证，优先用 `/qa`；如果只需要报告问题不改代码，优先用 `/qa-only`。
- 代码评审、检查 diff、查潜在回归与风险，优先用 `/review`。
- 更新发布文档、同步 README / runbook / 说明文档，优先用 `/document-release`。
- 每周回顾、阶段复盘，优先用 `/retro`。
- 设计系统、品牌、视觉方向探索，优先用 `/design-consultation`；视觉审查与设计修正，优先用 `/design-review`。
- 架构评审、数据流、边界条件、测试设计，优先用 `/plan-eng-review`。
- 安全审计、威胁建模、OWASP / STRIDE 视角检查，优先用 `/cso`。

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
