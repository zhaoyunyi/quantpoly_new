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

# spec/ 目录规范索引（必读）

除上述 OpenSpec 工作流外，本仓库还在 `spec/` 目录维护了更偏“落地实现/测试/建模”的规范。进行任何实现、测试、命名建模相关的工作前，请先阅读并遵守：

- `spec/ProgramSpec.md`：Specify Protocol（核心开发三原则）
  - **Library-First**：任何功能必须先抽为可复用的独立库
  - **CLI Mandate**：每个库必须提供 CLI（stdin/args/files 输入，stdout 输出，支持 JSON）
  - **Test-First**：严格 TDD；先写并确认失败的测试（Red）再写实现
- `spec/DDDSpec.md`：DDD 核心原则（通用语言 / 限界上下文 / 聚合与充血模型）
- `spec/BDD_TestSpec.md`：BDD 测试与输出格式规范（Given/When/Then；snake_case 分层日志输出）

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
