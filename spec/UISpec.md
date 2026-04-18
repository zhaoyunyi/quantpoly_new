# QuantPoly 设计系统规范（UISpec）

> **版本**：3.0 · **更新日期**：2026-04-17
>
> 本规范是 QuantPoly 前端 UI/UX 的**唯一事实来源（Single Source of Truth）**。
> 所有前端代码、Design Token、UI 组件和页面实现都必须遵守本规范；AI 编码助手在生成或修改前端代码时同样适用。

---

## 0. 设计原则

- **理性可信**：视觉的第一目标是建立可信度，而不是制造刺激。
- **结论优先**：页面应先展示用户最关心的结论或状态，再展开数据与细节。
- **可解释**：关键指标、风险信息、异常提示必须可被解释，不依赖隐含语义。
- **克制科技感**：避免过度装饰、重渐变、夸张阴影或过饱和色彩。
- **可访问性优先**：所有交互元素必须具备键盘可达与清晰焦点反馈。

---

## 0.1 Token 两层架构

当前项目采用两层 UI 约束架构：

1. **Design Token 层**：
   - 权威来源：`apps/frontend_web/design-tokens/tokens.json`（W3C DTCG 格式）
   - CSS 实现：`apps/frontend_web/app/styles/app.css` 中 `:root` / `.dark` 定义 CSS 变量
   - Tailwind 注册：`@theme {}` 块引用 `var(--color-xxx)` 完成 Tailwind 类名映射
2. **Utility / Component 层**：通过 `@layer utilities` 和 `libs/ui_design_system/` 中的组件封装，把 Token 转成可复用的类名和组件 API。

关键原则：

- 颜色、间距、圆角、阴影**不得在业务组件中硬编码**。
- 组件内部只能消费 Token 或 `libs/ui_design_system/` 暴露的封装能力。
- 如需新增视觉语义，应先更新 `tokens.json` → `app.css` → 本规范，再更新组件实现。
- Token 同步校验：`npm run validate:tokens`；硬编码颜色扫描：`npm run tokens:lint`。

---

## 0.2 可访问性标准

### 对比度要求

- 正文文本对比度应满足 WCAG AA，至少 **4.5:1**。
- 大字号标题与关键指标文本至少 **3:1**。
- 非文本元素（边框、图标、输入框状态）至少 **3:1**。

### 交互与语义

- 所有交互元素必须有清晰的 `focus-visible` 或等价焦点样式。
- 表单控件必须与 `<label>` 或等价可访问名称绑定。
- 错误提示必须与具体字段绑定，并能被辅助技术识别。
- 图标不能作为唯一信息来源，必要时必须有文字补充。

---

## 1. 技术栈与工具

| 层级 | 当前选型 | 备注 |
|------|----------|------|
| 页面框架 | **TanStack Start + React 19** | Web 应用主框架 |
| CSS 框架 | **Tailwind CSS v4** | 使用 `@theme` + `:root` / `.dark` 定义 Token |
| 色彩空间 | **OKLCH** | 所有颜色 Token 使用 OKLCH 定义 |
| 无头组件 | **Base UI** (`@base-ui/react`) | 底层交互能力 |
| UI 封装 | `libs/ui_design_system/` | Button / TextField / Select / Dialog / Table / Toast / Skeleton / ThemeProvider |
| 图标库 | **Lucide React** | 统一图标来源，禁止内联 SVG 和 emoji 图标 |
| 主题切换 | `ThemeProvider` + `useTheme()` | 支持 light / dark / system |
| 类名工具 | `cn()` = `clsx` 封装 | 见 `libs/ui_design_system/src/utils.ts` |
| 组件测试 | **Vitest + Testing Library** | 组件与页面单元/UI 测试 |
| E2E 测试 | **Playwright** | 见 `apps/frontend_web/playwright.config.ts` |
| Token 权威来源 | `design-tokens/tokens.json` | W3C DTCG 格式，校验脚本: `npm run validate:tokens` |
| Token CSS 实现 | `app/styles/app.css` | `:root` (light) + `.dark` (dark) |

---

## 2. 配色系统（Color System）

### 2.1 颜色来源规则

- 所有颜色 Token 的权威来源是 `design-tokens/tokens.json`。
- CSS 变量定义在 `app/styles/app.css` 的 `:root`（light）和 `.dark`（dark）中。
- 所有颜色使用 **OKLCH** 色彩空间定义。
- 组件和页面中**禁止**直接书写 hex / rgb / hsl / oklch 字面值。
- 所有业务组件必须通过 Tailwind Token 类或语义 utility class 使用颜色。

### 2.2 当前核心 Token

#### 品牌主色（Primary）— H≈255° 靛蓝轴

| Token | Light | Dark | 推荐用途 |
|-------|-------|------|---------|
| `--color-primary-900` | `oklch(0.32 0.069 259)` | `oklch(0.80 0.08 259)` | 页面主标题、核心指标 |
| `--color-primary-700` | `oklch(0.46 0.103 255)` | `oklch(0.68 0.10 255)` | 主按钮、主图表线 |
| `--color-primary-500` | `oklch(0.58 0.107 253)` | `oklch(0.72 0.10 253)` | 链接、次级强调 |

#### 辅助色（Secondary）

| Token | Light | Dark | 推荐用途 |
|-------|-------|------|---------|
| `--color-secondary-500` | `oklch(0.57 0.079 269)` | `oklch(0.70 0.07 269)` | 辅助说明、边界区分 |
| `--color-secondary-300` | `oklch(0.72 0.061 259)` | `oklch(0.50 0.05 259)` | 轻边框、弱强调 |

#### 背景与文本

| Token | Light | Dark | 推荐用途 |
|-------|-------|------|---------|
| `--color-bg-page` | `oklch(0.98 0.004 271)` | `oklch(0.16 0.01 260)` | 页面主背景 |
| `--color-bg-card` | `oklch(1.00 0 0)` | `oklch(0.22 0.01 260)` | 卡片、对话框 |
| `--color-bg-subtle` | `oklch(0.95 0.009 265)` | `oklch(0.25 0.01 260)` | 弱背景、交替行 |
| `--color-text-primary` | `oklch(0.26 0.030 265)` | `oklch(0.93 0.005 260)` | 主正文、标题 |
| `--color-text-secondary` | `oklch(0.51 0.032 258)` | `oklch(0.72 0.02 260)` | 次级文本、标签 |
| `--color-text-muted` | `oklch(0.67 0.029 262)` | `oklch(0.55 0.02 262)` | 注释、时间戳 |
| `--color-text-on-primary` | `oklch(1.00 0 0)` | `oklch(1.00 0 0)` | 主色背景上的文字 |

#### 状态色

| Token | Light | Dark | 推荐用途 | 约束 |
|-------|-------|------|---------|------|
| `--color-state-up` | `oklch(0.53 0.100 23)` | `oklch(0.65 0.12 23)` | 上涨数值 | 仅限数值与状态标识 |
| `--color-state-down` | `oklch(0.55 0.067 160)` | `oklch(0.65 0.08 160)` | 下跌数值 | 仅限数值与状态标识 |
| `--color-state-risk` | `oklch(0.64 0.119 60)` | `oklch(0.72 0.12 60)` | 风险提示 | 不得大面积装饰性使用 |
| `--color-state-disabled` | `oklch(0.83 0.017 259)` | `oklch(0.40 0.015 260)` | 禁用态 | 应与透明度规则配合 |

#### 图表色

| Token | Light | Dark | 推荐用途 |
|-------|-------|------|---------|
| `--color-chart-primary` | `oklch(0.46 0.103 255)` | `oklch(0.68 0.10 255)` | 主数据曲线 |
| `--color-chart-secondary` | `oklch(0.57 0.079 269)` | `oklch(0.70 0.07 269)` | 对比曲线 |
| `--color-chart-grid` | `oklch(0.92 0.013 262)` | `oklch(0.30 0.01 262)` | 网格线 |
| `--color-chart-axis` | `oklch(0.71 0.029 260)` | `oklch(0.55 0.025 260)` | 坐标轴与刻度 |

#### 边框与焦点

| Token | Light | Dark | 推荐用途 |
|-------|-------|------|---------|
| `--color-border` | `oklch(0.90 0.008 262)` | `oklch(0.35 0.01 260)` | 默认边框 |
| `--color-ring` | `oklch(0.58 0.107 253)` | `oklch(0.72 0.10 253)` | 焦点环 |

### 2.3 Surface / Foreground 推荐配对

| Surface | Foreground | 用途 |
|---------|-----------|------|
| `bg-bg-page` | `text-text-primary` | 页面默认背景与正文 |
| `bg-bg-card` | `text-text-primary` | 卡片、表单、对话框 |
| `bg-bg-subtle` | `text-text-secondary` | 弱背景、次级信息区 |
| `bg-primary-700` | `text-text-on-primary` | 主按钮、主 CTA |

### 2.4 Dark Mode 规范

- 主题切换通过 `ThemeProvider`（`libs/ui_design_system/src/ThemeProvider.tsx`）管理。
- 支持三种模式：`light` / `dark` / `system`（跟随系统偏好）。
- 用户偏好持久化在 `localStorage`（key: `qp-theme`）。
- 通过在 `<html>` 元素上切换 `.dark` class 实现主题切换。
- 所有颜色 Token 在 `:root` 和 `.dark` 中分别定义，组件通过 `var()` 引用自动适配。
- 新增组件或页面**必须**在 light 和 dark 两种主题下验证视觉效果。

### 2.5 禁止规则

- 禁止在业务组件中直接写 `#fff`、`#000`、`rgb(...)`、`hsl(...)`、`oklch(...)` 字面值。
- 禁止用红绿色做大面积装饰或主导航色。
- 禁止绕过 Token 体系引入额外”临时色板”。
- 禁止使用 `bg-white`、`text-black` 等非语义类名。

---

## 3. 字体规范（Typography）

### 3.1 字体族

| 变量 | 值 |
|------|----|
| `--font-sans` | `'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| `--font-mono` | `'JetBrains Mono', 'Menlo', monospace` |

### 3.2 基础字号

| Token | 值 |
|------|----|
| `--text-h1` | `28px` |
| `--text-h2` | `22px` |
| `--text-h3` | `18px` |
| `--text-body` | `14px` |
| `--text-caption` | `12px` |

### 3.3 规范化文本样式

| Utility Class | 用途 |
|---------------|------|
| `text-title-page` | 页面标题 |
| `text-title-section` | 区块标题 |
| `text-title-card` | 卡片标题 |
| `text-data-primary` | 关键指标与主要数值 |
| `text-data-secondary` | 次级数值与辅助指标 |
| `text-data-mono` | 日期、金额、代码、序列号 |
| `text-body` | 正文 |
| `text-body-secondary` | 次级正文 |
| `text-caption` | 辅助标签 |
| `text-disclaimer` | 免责声明与弱提示 |

### 3.4 字体使用规则

- 页面标题、区块标题、卡片标题最多使用 `font-medium` 或等价层级。
- 核心数值优先使用等宽字体（`font-mono` 或 `data-mono`）。
- 免责声明、风险提示和指标解释不得省略。

---

## 4. 间距规范（Spacing）

### 4.1 设计 Token

| Token | 值 |
|------|----|
| `--space-xs` | `4px` |
| `--space-sm` | `8px` |
| `--space-md` | `16px` |
| `--space-lg` | `24px` |
| `--space-xl` | `32px` |
| `--space-2xl` | `48px` |

### 4.2 推荐使用方式

| Utility | 用途 |
|---------|------|
| `gap-xs` / `gap-sm` / `gap-md` / `gap-lg` | 组件与列表间距 |
| `p-sm` / `p-md` / `p-lg` / `p-xl` | 容器内边距 |
| `px-*` / `py-*` 系列 | 水平/垂直内边距 |
| `mt-*` / `mb-*` 系列 | 段落与模块节奏控制 |

### 4.3 规则

- 间距必须按 4px 倍数体系组织。
- 避免在业务代码中出现“临时微调”的散乱值。
- 组件内部优先使用规范 utility class，而不是重复内联样式。

---

## 5. 圆角与阴影规范

### 5.1 圆角

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--radius-sm` | `4px` | 按钮、输入框、小徽章 |
| `--radius-md` | `8px` | 卡片、对话框、较大容器 |

规则：

- 禁止大面积使用超大圆角制造“消费级卡片感”。
- 输入框、按钮、表格内交互元素优先使用 `rounded-sm`。

### 5.2 阴影

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--shadow-card` | `0 4px 12px rgba(0, 0, 0, 0.06)` | 卡片、浮层轻阴影 |

规则：

- 页面默认不依赖大阴影分层。
- 卡片与浮层尽量只使用单层轻阴影。
- 禁止高模糊、重投影或多层叠加阴影。

---

## 6. 交互与状态规范

### 6.1 基础交互基线

当前项目在 `libs/ui_design_system/src/utils.ts` 中统一暴露：

- `focusRingClass`：焦点环样式
- `disabledClass`：禁用态样式
- `transitionClass`：基础过渡样式
- `cn()`：类名组合函数

### 6.2 组件最小状态集

所有交互组件至少覆盖以下状态：

- `default`
- `hover`
- `focus-visible`
- `disabled`
- `loading`（如适用）
- `error`（如适用）

### 6.3 过渡规范

- 默认过渡基线为 `120ms ease-out`。
- 仅在确有必要时使用 `transition-all`。
- 禁止引入弹簧、回弹或高戏剧化动画作为默认交互。

---

## 7. 组件规范（UI Design System）

### 7.1 统一入口

统一从 `libs/ui_design_system/src/index.ts` 暴露组件与工具，避免业务层直接依赖底层实现细节。

当前核心组件包括：

- `Button`
- `TextField`
- `Select`
- `Dialog`
- `ToastProvider` / `useToast`
- `ThemeProvider` / `useTheme`
- `Table`
- `Skeleton` / `Spinner` / `EmptyState`
- `cn` / `focusRingClass` / `disabledClass` / `transitionClass`

### 7.2 Button

当前 `Button` 规范：

- 变体：`primary` / `secondary` / `ghost`
- 尺寸：`sm` / `md` / `lg`
- 状态：`default` / `hover` / `focus-visible` / `disabled` / `loading`

业务页面应优先复用 `Button`，而不是手写按钮样式。

### 7.3 TextField

当前 `TextField` 规范：

- 支持 `label`、`help`、`error`
- 支持 `startAdornment` / `endAdornment`
- 错误态必须通过 `aria-invalid` 和关联描述暴露给辅助技术

### 7.4 ThemeProvider

- 通过 `<ThemeProvider>` 包裹应用根节点（已在 `entry_wiring.tsx` 中接入）。
- `useTheme()` 返回 `{ theme, resolved, setTheme }`。
- `theme`：用户选择的模式（`light` / `dark` / `system`）。
- `resolved`：实际生效的模式（`light` / `dark`）。
- `setTheme(t)`：切换主题并持久化。

### 7.5 图标规范（Lucide React）

- 统一使用 **Lucide React** 作为图标来源。
- **禁止**内联 SVG、emoji 图标或其他图标库。
- 导入方式：`import { IconName } from 'lucide-react'`。

#### 尺寸规范

| 场景 | Tailwind 类 | 像素 |
|------|------------|------|
| 内联文本 | `size-4` | 16px |
| 按钮/表单 | `size-5` | 20px |
| 卡片/导航 | `size-6` | 24px |
| 大图标 | `size-8` | 32px |

#### 使用规则

- 图标颜色通过 `text-*` Token 类控制，不使用 `fill` 或 `stroke` 属性。
- 纯装饰图标必须添加 `aria-hidden=”true”`。
- 图标按钮必须有 `aria-label`。
- 图标不能作为唯一信息来源，必要时必须有文字补充。

### 7.6 其他组件

- `Select`、`Dialog` 基于 Base UI 封装，业务代码不直接耦合底层库。
- `Table` 必须服务于数据可读性，不得为了”科技感”牺牲对齐与可扫描性。
- `Toast` 仅用于瞬时反馈，不替代表单级错误提示。
- `Skeleton` / `Spinner` / `EmptyState` 负责 loading / 空态体验的一致性。

---

## 8. 页面与信息架构

### 8.1 当前一级页面域

当前前端路由和页面能力主要围绕以下域展开：

- Landing / Auth
- Dashboard
- Strategies
- Backtests
- Trading
- Monitor
- Settings

### 8.2 页面结构原则

1. **结论优先**：先展示结果、状态、异常，再展示明细。
2. **层级递进**：标题 → 关键指标 → 图表 / 列表 → 说明 / 风险 / 免责声明。
3. **关键操作明确**：每个页面都应明确主操作与次操作。
4. **弱化装饰**：视觉元素为信息服务，避免装饰性 UI 干扰数据阅读。

### 8.3 图表原则

- 图表应优先服务于解释和比较，而不是吸引注意。
- 轴线、网格线、标签必须足够克制，避免与主曲线争抢视觉优先级。
- 价格、权益、收益率、时间序列等数值标签优先使用等宽数字。

---

## 9. CSS 架构与实现约束

### 9.1 权威来源

- Design Tokens（JSON）：`apps/frontend_web/design-tokens/tokens.json`
- Design Tokens（CSS）：`apps/frontend_web/app/styles/app.css`（`:root` + `.dark`）
- 组件实现：`libs/ui_design_system/src/`
- 业务页面与 Widget：`apps/frontend_web/app/`

### 9.2 实现规则

- 组件中禁止硬编码颜色与阴影值。
- 类名组合必须通过 `cn()` 完成。
- 共享交互样式优先通过 `focusRingClass`、`disabledClass`、`transitionClass` 复用。
- 如需新增公共视觉语义，优先更新 `tokens.json` → `app.css` → UI 组件库，而不是在业务代码局部发明一套规则。
- 新增 Token 后必须运行 `npm run validate:tokens` 确认同步。

---

## 10. 测试与验收规范

### 10.1 测试分层

| 层级 | 工具 | 目标 |
|------|------|------|
| 单元 / 组件测试 | Vitest + Testing Library | 组件 API、交互状态、无障碍断言 |
| 页面测试 | Vitest + Testing Library | 页面数据流、错误态、空态、关键文案 |
| E2E | Playwright | 关键流程稳定回归 |

### 10.2 相关规范

- BDD 表达方式遵循 `spec/BDD_TestSpec.md`
- 浏览器测试选型遵循 `spec/BrowserTestStrategy.md`

### 10.3 最低验收清单

- [ ] 颜色、间距、圆角、阴影均来自 Token 或公共 utility
- [ ] 交互组件具备 `focus-visible`、`disabled`、`error` 等必要状态
- [ ] 组件与页面具备可访问标签与错误反馈
- [ ] 页面主流程具备对应测试覆盖
- [ ] 关键业务页面至少能通过 Playwright 或等价流程验证

---

## 11. AI 执行清单

AI 助手新增或修改前端代码时，必须至少检查：

- [ ] 是否优先复用了 `libs/ui_design_system` 中已有组件
- [ ] 是否使用了 `cn()` 组合类名
- [ ] 是否避免了硬编码颜色值（使用 `npm run tokens:lint` 验证）
- [ ] 是否保持了当前 Token 体系和 utility class 语义
- [ ] 是否补齐了 `focus-visible` / `disabled` / `error` 等状态
- [ ] 是否使用 Lucide React 图标（禁止内联 SVG / emoji）
- [ ] 是否在 light 和 dark 两种主题下验证了视觉效果
- [ ] 新增 Token 是否已同步到 `tokens.json` 和 `app.css`
- [ ] 是否为新增页面或关键组件补充了 Vitest / Playwright 级验证

---

## 12. 变更历史

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-04-17 | v3.0: OKLCH 迁移、tokens.json (W3C DTCG)、Dark Mode、ThemeProvider、Lucide React、校验脚本 | Claude Code |
| 2026-04-18 | v2.0: 基于外部新版设计系统规范结构重写，并按 QuantPoly 当前技术栈适配 | Codex |
