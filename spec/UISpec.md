# QuantPoly 设计系统规范（UISpec）

> **版本**：2.0 · **更新日期**：2026-04-18
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

1. **Design Token 层**：定义在 `apps/frontend_web/app/styles/app.css` 的 `@theme {}` 中，是颜色、字体、间距、圆角、阴影、动画等视觉值的唯一真实来源。
2. **Utility / Component 层**：通过 `@layer utilities` 和 `libs/ui_design_system/` 中的组件封装，把 Token 转成可复用的类名和组件 API。

关键原则：

- 颜色、间距、圆角、阴影**不得在业务组件中硬编码**。
- 组件内部只能消费 Token 或 `libs/ui_design_system/` 暴露的封装能力。
- 如需新增视觉语义，应先更新 `app/styles/app.css` 和本规范，再更新组件实现。

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
| CSS 框架 | **Tailwind CSS v4** | 使用 `@theme` 定义 Token |
| 无头组件 | **Base UI** (`@base-ui/react`) | 底层交互能力 |
| UI 封装 | `libs/ui_design_system/` | 统一暴露 Button / TextField / Select / Dialog / Table / Toast / Skeleton |
| 类名工具 | `cn()` = `clsx` 封装 | 见 `libs/ui_design_system/src/utils.ts` |
| 组件测试 | **Vitest + Testing Library** | 组件与页面单元/UI 测试 |
| E2E 测试 | **Playwright** | 见 `apps/frontend_web/playwright.config.ts` |
| Token 权威来源 | `apps/frontend_web/app/styles/app.css` | 当前唯一真实来源 |

---

## 2. 配色系统（Color System）

### 2.1 颜色来源规则

- 所有颜色 Token 定义在 `apps/frontend_web/app/styles/app.css`。
- 组件和页面中**禁止**直接书写 hex / rgb / hsl。
- 所有业务组件必须通过 Tailwind Token 类或语义 utility class 使用颜色。

### 2.2 当前核心 Token

#### 品牌主色（Primary）

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--color-primary-900` | `#1B3255` | 页面主标题、核心指标、深色主强调 |
| `--color-primary-700` | `#2D5990` | 主按钮、主图表线、主导航选中态 |
| `--color-primary-500` | `#4A7DB8` | 链接、次级强调、可交互高亮 |

#### 辅助色（Secondary）

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--color-secondary-500` | `#6374A5` | 辅助说明、边界区分、次级信息 |
| `--color-secondary-300` | `#8DA5CA` | 轻边框、弱强调、背景分层 |

#### 背景与文本

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--color-bg-page` | `#F7F8FB` | 页面主背景 |
| `--color-bg-card` | `#FFFFFF` | 卡片、对话框、浮层主体 |
| `--color-bg-subtle` | `#EDF0F6` | 弱背景、表格交替行、分区背景 |
| `--color-text-primary` | `#1D2433` | 主正文、标题说明 |
| `--color-text-secondary` | `#5B6779` | 次级文本、标签、辅助说明 |
| `--color-text-muted` | `#8C96A8` | 注释、时间戳、免责声明 |
| `--color-text-on-primary` | `#FFFFFF` | 主色背景上的前景文字 |

#### 状态色

| Token | 值 | 推荐用途 | 约束 |
|------|----|---------|------|
| `--color-state-up` | `#9E5350` | 上涨数值 | 仅限数值与状态标识 |
| `--color-state-down` | `#4D7D63` | 下跌数值 | 仅限数值与状态标识 |
| `--color-state-risk` | `#BF7838` | 风险提示、错误边界 | 不得大面积装饰性使用 |
| `--color-state-disabled` | `#C1C8D3` | 禁用态 | 应与透明度规则配合 |

#### 图表色

| Token | 值 | 推荐用途 |
|------|----|---------|
| `--color-chart-primary` | `#2D5990` | 主数据曲线 |
| `--color-chart-secondary` | `#6374A5` | 对比曲线 |
| `--color-chart-grid` | `#E0E5EE` | 网格线 |
| `--color-chart-axis` | `#96A1B3` | 坐标轴与刻度 |

### 2.3 Surface / Foreground 推荐配对

| Surface | Foreground | 用途 |
|---------|-----------|------|
| `bg-bg-page` | `text-text-primary` | 页面默认背景与正文 |
| `bg-bg-card` | `text-text-primary` | 卡片、表单、对话框 |
| `bg-bg-subtle` | `text-text-secondary` | 弱背景、次级信息区 |
| `bg-primary-700` | `text-text-on-primary` | 主按钮、主 CTA |

### 2.4 禁止规则

- 禁止在业务组件中直接写 `#fff`、`#000`、`rgb(...)`、`hsl(...)`。
- 禁止用红绿色做大面积装饰或主导航色。
- 禁止绕过 Token 体系引入额外“临时色板”。

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

### 7.4 其他组件

- `Select`、`Dialog` 基于 Base UI 封装，业务代码不直接耦合底层库。
- `Table` 必须服务于数据可读性，不得为了“科技感”牺牲对齐与可扫描性。
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

- Design Tokens：`apps/frontend_web/app/styles/app.css`
- 组件实现：`libs/ui_design_system/src/`
- 业务页面与 Widget：`apps/frontend_web/app/`

### 9.2 实现规则

- 组件中禁止硬编码颜色与阴影值。
- 类名组合必须通过 `cn()` 完成。
- 共享交互样式优先通过 `focusRingClass`、`disabledClass`、`transitionClass` 复用。
- 如需新增公共视觉语义，优先扩展 `app.css` 或 UI 组件库，而不是在业务代码局部发明一套规则。

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
- [ ] 是否避免了硬编码颜色值
- [ ] 是否保持了当前 Token 体系和 utility class 语义
- [ ] 是否补齐了 `focus-visible` / `disabled` / `error` 等状态
- [ ] 是否为新增页面或关键组件补充了 Vitest / Playwright 级验证

---

## 12. 变更历史

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-04-18 | 基于外部新版设计系统规范结构重写，并按 QuantPoly 当前技术栈适配 | Codex |
