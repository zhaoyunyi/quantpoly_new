# 前端建设文档入口（docs/frontend）

## 1. 核心规范

- `spec/UISpec.md`
- `spec/FrontendArchitectureSpec.md`
- `spec/DesignTokensSpec.md`

## 2. 设计与实现原则

- 遵循 `spec/ProgramSpec.md`：Library-First、CLI Mandate、Test-First
- 遵循 `spec/DDDSpec.md`：限界上下文与通用语言一致
- 前端仅作为后端能力的 UI 与交互层，不承载用户系统主逻辑

## 3. 当前实现状态

- 前端应用框架已落位为 `TanStack Start`（目录：`apps/frontend_web/`）
- 前端子项目说明：`apps/frontend_web/AGENTS.md`
- 关键运行命令：
  - `cd apps/frontend_web && npm run dev`
  - `cd apps/frontend_web && npm run build`
  - `cd apps/frontend_web && npm run start`
