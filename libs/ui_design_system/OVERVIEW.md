# UI 设计系统库（ui_design_system）

本目录承载可复用的 UI 设计系统能力，约束为：

- Base UI（无头组件）+ Tailwind CSS v4
- 视觉样式来自 Design Tokens（`apps/frontend_web/app/styles/app.css` 的 `@theme {}`）
- 组件覆盖基础交互状态（default/hover/focus/disabled/loading/error），并满足键盘可达/焦点可见

## 组件

- `Button`
- `TextField`
- `Select`（Base UI）
- `Dialog`（Base UI）
- `Toast`（最小实现）
- `Table`
- `Skeleton / Spinner / EmptyState`

## Tokens CLI

校验 `app.css` 中的 `@theme` tokens，stdout 输出 JSON；缺失必需 tokens 会返回非 0 exit code。

```bash
node libs/ui_design_system/cli.mjs
node libs/ui_design_system/cli.mjs --css-path apps/frontend_web/app/styles/app.css
```
