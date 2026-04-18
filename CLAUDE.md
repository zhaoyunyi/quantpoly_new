# CLAUDE.md

本文件是 Claude Code / AI 编码助手在当前仓库的精简入口。公共背景与重复索引已抽到：

- `docs/guides/ai-collaboration.md`
- `docs/guides/ai-context-index.md`
- `docs/README.md`

## 必读顺序

1. `README.md`
2. `docs/guides/ai-collaboration.md`
3. `docs/guides/ai-context-index.md`
4. `openspec/AGENTS.md`（涉及计划 / 提案 / 规格 / 变更时）
5. 当前工作目录下的 `CLAUDE.md` 或 `AGENTS.md`
6. 实际代码与测试

## 协作约定

- 当前事实优先看 `README.md`、`docs/README.md`、`docs/migration/2026-02-13-backend-current-state.md`、`openspec/specs/`
- 开发中变更优先看 `openspec/changes/`
- 落地开发、浏览器测试、UI 与前端架构约束优先看 `spec/`
- 本仓库本地版本控制使用 `jj`
- 执行 OpenSpec CLI 时优先使用 `scripts/openspecw.sh`
- `docs/plans/` 默认是历史计划或工作草稿，不等于当前产品事实

## 目录入口

- `apps/backend_app/AGENTS.md`
- `apps/frontend_web/AGENTS.md`
- `deploy/AGENTS.md`
- `docs/frontend/AGENTS.md`
- `libs/frontend_api_client/AGENTS.md`
- `libs/ui_app_shell/AGENTS.md`
- `libs/ui_design_system/AGENTS.md`

## 重要直达索引

- 协作入口：`docs/guides/ai-collaboration.md`
- 上下文地图：`docs/guides/ai-context-index.md`
- OpenSpec：`openspec/AGENTS.md`
- 规范：`spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`、`spec/BrowserTestStrategy.md`、`spec/UISpec.md`
- 后端组合入口：`apps/backend_app/AGENTS.md`
- 前端规范入口：`docs/frontend/AGENTS.md`、`apps/frontend_web/AGENTS.md`
- 部署入口：`deploy/AGENTS.md`
- 后端运行与门禁：`docs/runbooks/backend-operations-runbook.md`、`docs/gates/backend-gate-handbook.md`
- Skill 约定、多 Agent 约束与 `jj` 工作流：`AGENTS.md`

## gstack

- 当前仓库允许按需使用 `gstack` 的 slash workflows。
- 涉及网页浏览、站点验证、截图、交互式 QA 时，优先使用 `gstack` 的 `/browse`、`/qa`、`/qa-only`、`/open-gstack-browser`。
- 常用流程命令包括：`/office-hours`、`/autoplan`、`/review`、`/investigate`、`/ship`、`/cso`。
- 使用 `gstack` 相关文件路径时，优先使用全局安装路径 `~/.claude/skills/gstack/...`。
- 不使用 `mcp__claude-in-chrome__*` 作为本仓库默认网页浏览方案。

## Skill routing

适用范围：仅适用于已安装 `gstack` 的 Claude Code 会话。对于不支持 `gstack` slash workflows 的宿主，不要求模拟这些命令。

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
