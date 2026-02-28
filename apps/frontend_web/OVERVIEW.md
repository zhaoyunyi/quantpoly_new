# 前端应用（frontend_web）

## 1. 目标

本目录用于承载 QuantPoly 前端应用（Web）。

- 前端仅负责 UI 呈现、交互编排、调用后端 API。
- 用户认证、会话签发、权限判断等能力继续由后端负责。

## 2. 目录约定

- `app/`：TanStack Start 路由与页面源码
- `tests/`：前端测试目录（按需扩展）
- `app.config.ts`：TanStack Start 应用配置
- `package.json`：前端依赖与脚本

## 3. 框架与命令

- 当前前端框架：`TanStack Start`（React）
- 开发启动：`cd apps/frontend_web && npm run dev`
- 生产构建：`cd apps/frontend_web && npm run build`
- 本地预览：`cd apps/frontend_web && npm run start`

## 4. 边界说明

- 当前提交完成 TanStack Start 脚手架落位，不改变后端运行路径。
- 现有后端入口 `apps/backend_app/` 与脚本命令保持不变。
