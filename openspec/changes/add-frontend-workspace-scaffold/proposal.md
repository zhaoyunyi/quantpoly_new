# Change: add-frontend-workspace-scaffold

## Why

当前仓库已完成后端主能力重构，但缺少前端应用落位与 UI 规范基线，导致前后端协作边界不完整。

## What Changes

- 新增前端应用目录 `apps/frontend_web/`。
- 在 `apps/frontend_web/` 下采用 `TanStack Start` 作为前端框架，并提供可运行脚手架。
- 新增前端相关库目录占位：`libs/ui_design_system/`、`libs/ui_app_shell/`、`libs/frontend_api_client/`。
- 新增前端规范文档：`spec/UISpec.md`、`spec/FrontendArchitectureSpec.md`、`spec/DesignTokensSpec.md`。
- 新增 `docs/frontend/OVERVIEW.md` 作为前端文档入口。
- 为解决上游子包漂移导致的构建不稳定，锁定 TanStack 关键依赖版本策略（`package.json` + `overrides`）。

## Impact

- Affected specs: `frontend-foundation`（新增）
- Affected code: 新增前端脚手架与规范文档；不修改现有后端应用与后端库运行链路
