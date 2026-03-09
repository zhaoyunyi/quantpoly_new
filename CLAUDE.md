# CLAUDE.md

本文件用于 Claude Code（claude.ai/code）在本仓库协作时的入口指引。

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

本仓库的协作规范与命令入口统一维护在根目录 `AGENTS.md`（以及 `openspec/AGENTS.md`、`spec/` 目录）。

请优先阅读：

- `AGENTS.md`
- `openspec/AGENTS.md`
- `spec/ProgramSpec.md`
- `spec/DDDSpec.md`
- `spec/BDD_TestSpec.md`
- `spec/UISpec.md`
- `spec/FrontendArchitectureSpec.md`
- `spec/DesignTokensSpec.md`
