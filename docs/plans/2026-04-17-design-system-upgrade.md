# QuantPoly 设计系统升级方案

> **日期**：2026-04-17
> **范围**：tokens.json · OKLCH 迁移 · Dark Mode · Lucide Icons · 校验脚本 · 规范更新

---

## 1. 决策记录

- **Headless 层**：保留 Base UI，不引入 Radix UI / Shadcn/UI 组件层
- **色彩空间**：从 HEX 全量迁移到 OKLCH
- **Dark Mode**：完整实现（ThemeProvider + 所有组件适配）
- **图标库**：引入 Lucide React 替换内联 SVG / emoji
- **Token 格式**：W3C DTCG 格式 tokens.json，light/dark 双值

## 2. 实施步骤

### Step 1: tokens.json（W3C DTCG 格式）

- 创建 `apps/frontend_web/design-tokens/tokens.json`
- 所有现有 HEX token 转换为 OKLCH
- 每个 color token 包含 `light` / `dark` 双值
- 包含 color、radius、shadow、spacing、typography 分类

### Step 2: app.css OKLCH + Dark Mode 改造

- `:root` 定义 light 主题 CSS 变量（OKLCH 值）
- `.dark` 定义 dark 主题 CSS 变量（OKLCH 值）
- `@theme` 块引用 `var(--color-xxx)` 而非硬编码值
- 检查并替换所有硬编码颜色

### Step 3: ThemeProvider

- `libs/ui_design_system/src/ThemeProvider.tsx`
- 支持 light / dark / system
- localStorage 持久化（key: `qp-theme`）
- `<html>` 上切换 `.dark` class
- 暴露 `useTheme()` hook
- 从 index.ts 导出

### Step 4: Lucide React

- 安装 `lucide-react` 依赖
- 替换现有内联 SVG / emoji 图标
- UISpec 新增图标规范

### Step 5: Token 校验脚本

- `apps/frontend_web/scripts/validate-tokens.mjs`
- 校验 tokens.json ↔ app.css 同步
- 扫描硬编码颜色
- package.json 新增 `validate:tokens` / `tokens:lint` 命令

### Step 6: 规范文档更新

- UISpec.md：OKLCH、dark mode、Lucide、配对表
- DesignTokensSpec.md：tokens.json 格式、校验流程
