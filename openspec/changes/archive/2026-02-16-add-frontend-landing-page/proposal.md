# Change: 前端 Landing 页面（Public）

## Why

Landing 页面承担产品介绍与转化入口（注册/登录），并需要符合当前仓库 UI 规范（理性可信、克制科技感、永远附带免责声明）。

## What Changes

- 实现 `/`（Landing）
- 提供明确 CTA：注册/登录
- 可选展示后端运行状态（`GET /health`）

## Impact

- Affected code:
  - `apps/frontend_web/app/routes/index.tsx`
- Affected specs:
  - `frontend-landing`

