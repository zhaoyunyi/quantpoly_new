## Context

当前前端工作区 `apps/frontend_web` 以 TanStack Start 为框架基线，但实际运行时仍依赖旧版 Vinxi CLI 与一组版本锁定/overrides。仓库已经验证当前 `npm run build` 可以通过，但会出现两类 warning：

- TanStack Start 旧 runtime 内部触发的 `node:fs/node:path externalized for browser compatibility`
- 第三方组件库在 server bundling 过程中暴露的 `'use client' was ignored`

这两类 warning 性质不同。此次迁移的目标是收敛第一类运行时 warning，并把第二类 warning 的归因与处置边界记录清楚。

## Goals / Non-Goals

- Goals:
  - 迁移到基于 TanStack Start 官方 Vite 集成的运行时基线
  - 消除旧 Vinxi runtime 相关的 browser externalization warning
  - 清理不再需要的 Start internal overrides，降低版本漂移
  - 保持现有页面行为、测试入口与基础开发命令可用
  - 为迁移后的剩余 warning 提供可追踪的归因结论
- Non-Goals:
  - 不在本次变更中重写业务页面或 UI 结构
  - 不承诺一次性消除所有第三方 bundling warning
  - 不同时引入新的状态管理、SSR 数据预取或部署平台迁移

## Decisions

- Decision: 将迁移范围限定为前端基础设施层，不修改业务能力边界。
  - Alternatives considered:
    - 继续停留在旧 Vinxi 版本并仅做依赖微调：不能根治 runtime 基线偏移，后续仍会重复遇到同类 warning
    - 一次性同时升级 TanStack、Base UI、部署运行时：风险面过大，不利于隔离问题来源

- Decision: 保留 `npm test`、`npm run build`、`npm run dev` 这组开发命令语义不变，只替换底层实现。
  - Alternatives considered:
    - 同时改命令名与目录结构：对现有开发流程扰动过大，没有必要

- Decision: 将 warning 对比结果视为迁移交付物的一部分，并要求同步更新前端运行文档。
  - Alternatives considered:
    - 只看迁移后 build 是否通过：无法区分 warning 被消除、转移还是新增

- Decision: 将剩余第三方 warning 视为迁移后的审计结果，而不是本次变更的硬性阻断项。
  - Alternatives considered:
    - 要求所有 warning 归零后才允许迁移完成：会把框架迁移与第三方生态问题绑死，范围失控

## Risks / Trade-offs

- TanStack Start 当前版本跨度较大，`app.config.ts`、client/server entry、route manifest 集成方式可能需要同步调整。
  - Mitigation: 先完成最小脚手架迁移，再用现有前端测试和构建作为回归门禁。

- 清理 overrides 后，锁文件中可能暴露新的版本冲突或 peer dependency 问题。
  - Mitigation: 采用一次性对齐 TanStack family 版本的策略，不做零散升包。

- Base UI `'use client'` warning 可能在迁移后仍存在。
  - Mitigation: 将其标记为迁移后审计项；若仍存在，则记录具体来源、影响范围和是否需要后续单独提案。

## Migration Plan

1. 盘点当前前端运行时入口、脚本、overrides 与 lockfile 中的 Vinxi 依赖链，并保存当前 build warning 基线。
2. 引入新版 TanStack Start + Vite 插件配置，替换旧 Vinxi CLI 脚本。
3. 对齐 TanStack Start/Router 版本族并刷新 lockfile。
4. 适配必要的 client/server entry、route manifest 与测试配置。
5. 运行现有前端测试与生产构建，比较迁移前后 warning 结果。
6. 更新前端文档，注明迁移后的开发/构建基线与剩余已知 warning。

## Open Questions

- 迁移后是否仍需要单独的 `manualChunks` workaround，取决于新版 route manifest 生成行为。
- 迁移后是否仍保留 `app.config.ts` 作为主配置入口，还是完全转移到 `vite.config.ts`，需以目标版本实际集成方式为准。
