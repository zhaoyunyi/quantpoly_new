## 1. 迁移准备

- [x] 1.1 盘点 `apps/frontend_web` 中所有 Vinxi 入口、Start internal overrides 与锁文件耦合点
- [x] 1.2 保存迁移前 `npm run build` 的 warning 基线，区分 Start runtime warning 与第三方 warning
- [x] 1.3 确认目标 TanStack Start + Vite 版本组，并列出需要保留/删除的依赖
- [x] 1.4 明确迁移后必须保持不变的行为门禁：`npm test`、`npm run build`、Landing、AuthGuard、AppShell

## 2. 运行时迁移

- [x] 2.1 将前端脚本从 `vinxi dev/build/start` 切换到新版 TanStack Start + Vite 推荐链路
- [x] 2.2 调整前端配置文件，使 aliases、Tailwind、SSR/client entry 与 route manifest 在新链路下可工作
- [x] 2.3 对齐 TanStack Start/Router 版本族并刷新 `package-lock.json`
- [x] 2.4 按需调整 `vitest` / `playwright` 配置，确保测试入口在新链路下不回退
- [x] 2.5 删除不再需要的旧 Start internal overrides 与 Vinxi 专有依赖

## 3. 验证与收尾

- [x] 3.1 运行 `cd apps/frontend_web && npm test`
- [x] 3.2 运行 `cd apps/frontend_web && npm run build`
- [x] 3.3 对比迁移前后的 build 输出，验证旧 runtime 相关 warning 已消失且未引入新的未归因 warning
- [x] 3.4 更新 `apps/frontend_web/AGENTS.md` 与 `docs/frontend/AGENTS.md`，说明迁移后的运行时基线与已知限制
