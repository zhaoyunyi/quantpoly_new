# 设计令牌规范（DesignTokensSpec）

> **版本**：2.0 · **更新日期**：2026-04-17

## 1. 权威来源与格式

- Token 权威来源：`apps/frontend_web/design-tokens/tokens.json`
- 格式：[W3C Design Tokens Community Group (DTCG)](https://tr.designtokens.org/format/)
- 色彩空间：**OKLCH**（所有颜色 Token 必须使用 OKLCH 定义）
- 每个 color Token 包含 `light` / `dark` 双值

### tokens.json 结构示例

```json
{
  "$schema": "https://tr.designtokens.org/format/",
  "color": {
    "primary-700": {
      "$type": "color",
      "$value": {
        "light": "oklch(0.46 0.103 255)",
        "dark": "oklch(0.68 0.10 255)"
      },
      "$description": "Primary buttons, main chart lines"
    }
  }
}
```

## 2. 命名约束

- 设计令牌统一使用 `kebab-case`。
- 分类前缀固定：`color-`、`font-`、`space-`、`radius-`、`shadow-`、`z-`。
- 语义优先，不使用纯视觉命名（例如避免 `blue-500` 直接暴露到业务组件）。

## 3. 必备令牌分类

- 颜色：主色、辅助色、背景、文本、状态色、图表色、边框、焦点环
- 字体：字号、字族
- 间距：4 的倍数尺度（xs/sm/md/lg/xl/2xl）
- 圆角：sm / md
- 阴影：card（light/dark 双值）
- 过渡：base

## 4. Dark Mode Token 规则

- 每个 color Token 必须同时定义 `light` 和 `dark` 值。
- Dark 值的设计原则：
  - 背景色降低亮度（L 值 0.15–0.25）
  - 文本色提高亮度（L 值 0.70–0.93）
  - 品牌色适度提亮以保持可识别性
  - 状态色保持色相不变，适度提亮
- 阴影在 dark 模式下加深（更高 alpha 值）。

## 5. 使用约束

- 业务组件禁止硬编码颜色、字号、间距。
- 主题切换通过 CSS 变量层完成（`:root` / `.dark`），不直接修改组件样式值。
- 新增令牌需附带使用场景与兼容说明。
- 新增令牌必须同时更新 `tokens.json` 和 `app.css`。

## 6. CSS 变量映射

- `:root` 定义 light 主题 CSS 变量
- `.dark` 定义 dark 主题 CSS 变量
- `@theme {}` 块通过 `var(--color-xxx)` 引用，注册为 Tailwind 类名

## 7. 校验与工具

| 命令 | 用途 |
|------|------|
| `npm run validate:tokens` | 校验 tokens.json ↔ app.css 同步性 |
| `npm run tokens:lint` | 扫描业务代码中的硬编码颜色 |

- Token 变更后必须运行 `npm run validate:tokens` 确认同步。
- CI 中建议集成 `npm run tokens:lint` 防止硬编码颜色回归。

## 8. 输出约束

- 令牌需要可导出为 JSON（tokens.json）与 CSS Variables（app.css）两种格式。
- 令牌变更必须有版本记录与回滚策略。

## 9. 变更历史

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-04-17 | v2.0: 新增 tokens.json 格式规范、OKLCH、Dark Mode 规则、校验流程 | Claude Code |
