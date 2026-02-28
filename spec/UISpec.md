# UI 规范（UISpec）

## 1. 设计理念

QuantPoly 的视觉风格追求 **理性可信 · 克制科技感 · 可解释**。

- **让数据说话**：视觉不吸引注意，只辅助理解
- **结论优先原则**：先呈现结论，再展开细节
- **克制使用装饰色**：红绿仅限数值标注，辅助色 ≤ 15%
- **永远附带免责声明**

---

## 2. 技术栈

| 层级      | 技术选型                        |
| --------- | ------------------------------- |
| 框架      | TanStack Start + React 19      |
| 构建      | Vinxi 0.5.3 (Vite)             |
| 样式      | Tailwind CSS v4 (@theme)        |
| 无头组件  | Base UI (@base-ui/react 1.2)    |
| 类名工具  | clsx                            |

---

## 3. 色彩系统

### 3.1 色相统一原则

- 全局色相锚定 **H ≈ 215°–220°**（靛蓝灰轴）
- 品牌主色、辅助色、背景色、文本色、图表色均共享此色相轴
- 状态功能色（上涨/下跌/风险）允许脱离色相轴，但保持低饱和

### 3.2 品牌色 — Primary

| Token                  | Hex       | 用途                      |
| ---------------------- | --------- | ------------------------- |
| `color.primary.900`    | `#1B3255` | 主标题 / 核心指标数值     |
| `color.primary.700`    | `#2D5990` | 图表主线 / 导航选中态     |
| `color.primary.500`    | `#4A7DB8` | 选中态 / 次级强调 / 链接  |

### 3.3 品牌色 — Secondary

| Token                  | Hex       | 用途                      |
| ---------------------- | --------- | ------------------------- |
| `color.secondary.500`  | `#6374A5` | 冷紫辅助（≤15%）/ 次线    |
| `color.secondary.300`  | `#8DA5CA` | 模块区分 / 辅助装饰       |

### 3.4 背景色

| Token               | Hex       | 用途                      |
| -------------------- | --------- | ------------------------- |
| `color.bg.page`     | `#F7F8FB` | 页面主背景                |
| `color.bg.card`     | `#FFFFFF` | 卡片 / 模态框 / 面板      |
| `color.bg.subtle`   | `#EDF0F6` | 分割区域 / 表格交替行     |

> **禁止**：纯黑或深色背景。

### 3.5 文本色

| Token                 | Hex       | 用途                      |
| --------------------- | --------- | ------------------------- |
| `color.text.primary`  | `#1D2433` | 正文主文本 / 结论         |
| `color.text.secondary`| `#5B6779` | 次级说明 / 标签           |
| `color.text.muted`    | `#8C96A8` | 注释 / 免责声明 / 时间戳  |

### 3.6 状态色

| Token                  | Hex       | 用途                      | 约束           |
| ---------------------- | --------- | ------------------------- | -------------- |
| `color.state.up`       | `#9E5350` | 上涨数值                  | 仅限数值标注   |
| `color.state.down`     | `#4D7D63` | 下跌数值                  | 仅限数值标注   |
| `color.state.risk`     | `#BF7838` | 风险提示条                | 仅限提示区域   |
| `color.state.disabled` | `#C1C8D3` | 禁用 / 无数据状态         | opacity: 0.4   |

> **禁止**：红绿用于按钮、标题、装饰或大面积填充。

### 3.7 图表色

| Token                  | Hex       | 用途                      |
| ---------------------- | --------- | ------------------------- |
| `color.chart.primary`  | `#2D5990` | 策略净值曲线 / 主指标     |
| `color.chart.secondary`| `#6374A5` | 基准曲线 / 对比指标       |
| `color.chart.grid`     | `#E0E5EE` | 图表网格线（弱化）        |
| `color.chart.axis`     | `#96A1B3` | 坐标轴文字与刻度          |

---

## 4. 字体系统

### 4.1 字体族

| 变量          | 值                                              |
| ------------- | ----------------------------------------------- |
| `--font-sans` | `'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| `--font-mono` | `'JetBrains Mono', 'Menlo', monospace`          |

### 4.2 文本样式

| 样式名           | 字族       | 字号  | 字重    | 行高 | 用途               |
| ---------------- | ---------- | ----- | ------- | ---- | ------------------ |
| Title / Page     | Inter      | 28px  | Medium  | 1.2  | 页面标题           |
| Title / Section  | Inter      | 22px  | Medium  | 1.2  | 区域标题           |
| Title / Card     | Inter      | 18px  | Medium  | 1.2  | 卡片标题           |
| Data / Primary   | JetBrains  | 22px  | Medium  | 1.2  | 核心指标数值       |
| Data / Secondary | JetBrains  | 14px  | Regular | 1.5  | 变化率 / 辅助数值  |
| Data / Mono      | JetBrains  | 12px  | Regular | 1.5  | 日期 / 金额        |
| Body / Default   | Inter      | 14px  | Regular | 1.5  | 正文               |
| Body / Secondary | Inter      | 14px  | Regular | 1.5  | 次级说明           |
| Meta / Caption   | Inter      | 12px  | Regular | 1.5  | 图表标签 / 元数据  |
| Meta / Disclaimer| Inter      | 12px  | Regular | 1.7  | 免责声明           |

> **禁止**：Heavy/Black/ExtraBold 字重。仅使用 400 (Regular) 和 500 (Medium)。

---

## 5. 间距系统

基于 **4px 倍数**尺度：

| Token        | 值   | 用途                 |
| ------------ | ---- | -------------------- |
| `space.xs`   | 4px  | 最小间距             |
| `space.sm`   | 8px  | 紧凑间距             |
| `space.md`   | 16px | 默认间距             |
| `space.lg`   | 24px | 区块间距             |
| `space.xl`   | 32px | 大区块间距           |
| `space.2xl`  | 48px | 页面级间距           |

---

## 6. 圆角与阴影

| Token          | 值                             | 用途               |
| -------------- | ------------------------------ | ------------------ |
| `radius-sm`    | 4px                            | 控件 / 按钮 / 徽章 |
| `radius-md`    | 8px                            | 卡片 / 面板 / 弹窗 |
| `shadow-card`  | `0 4px 12px rgba(0,0,0,0.06)`  | 卡片唯一阴影       |

> **禁止**：圆角 ≥ 12px；多层叠加阴影；高模糊渐变阴影。

---

## 7. 交互规范

### 7.1 状态过渡

| 属性                     | 值                |
| ------------------------ | ----------------- |
| `state.hover.opacity`    | `0.92`            |
| `state.disabled.opacity` | `0.4`             |
| `transition.base`        | `120ms ease-out`  |

> **禁止**：弹性缓动（spring/bounce/elastic）、回弹效果。

### 7.2 组件状态

每个交互组件必须定义并验收以下状态:

- `default` — 默认态
- `hover` — 鼠标悬浮（opacity 0.92）
- `focus` — 键盘焦点（清晰可见的焦点环）
- `disabled` — 禁用态（opacity 0.4，cursor: not-allowed）
- `loading` — 加载中
- `error` — 错误态

### 7.3 可访问性

- 键盘可达：核心操作可通过 Tab 与 Enter/Space 完成
- 焦点可见：焦点态必须有清晰视觉反馈
- 表单错误必须与具体字段绑定，支持屏幕阅读器识别

---

## 8. 页面与信息架构

### 8.1 一级导航

仪表盘 · 策略管理 · 回测中心 · 交易账户 · 风控中心 · 实时监控 · 用户中心

### 8.2 页面结构原则

1. **结论优先** — 先核心结论卡片，再详细数据
2. **层级递进** — 标题 → 指标 → 图表 → 统计 → 假设 → 免责
3. 每页必须明确：主目标、关键操作、关键反馈（成功/失败/加载中）
4. 路由命名使用业务通用语言

### 8.3 布局栅格

- 最大内容宽度：1200px，居中
- 响应断点：sm (640px) / md (768px) / lg (1024px) / xl (1280px)
- 卡片间距：16px (gap-md)
- 容器内边距：32px (px-xl)

---

## 9. 组件清单

当前仅建立 Design Tokens 与样式基线。组件封装与实现（Base UI + Tailwind）后续统一在 `libs/ui_design_system/` 内落地。

组件实现的最小要求：

- 覆盖 `default/hover/focus/disabled/loading/error`
- 禁止硬编码颜色（hex/rgb），全部来自 Design Tokens
- 交互与可访问性满足本规范第 7 节

---

## 10. 图表设计原则

- 图表使用细线（1.5–2px）、低对比坐标轴
- 网格线弱化（`#E0E5EE`），坐标轴灰色（`#96A1B3`）
- 目标：**解释数据，而不是吸引注意**
- Y 轴标签使用等宽字体
- 交互性：hover 显示具体数值，区间选择器切换时间范围

---

## 11. 文案语气

| 场景       | 语气要求                             | 示例                                                   |
| ---------- | ------------------------------------ | ------------------------------------------------------ |
| 结论       | 客观陈述 + 数值佐证                  | "年化收益 12.34%，优于基准 +1.5pp"                     |
| 风险提示   | 中性、不制造恐慌                     | "回撤明显放大，建议关注适用性局限"                     |
| 免责声明   | 规范法律措辞                         | "不构成投资建议。回测结果不代表未来表现。"             |
| 空状态     | 引导下一步                           | "暂无回测数据。请先创建策略并提交回测。"               |

---

## 12. CSS 架构

### 12.1 文件结构

```
app/styles/app.css          # Tailwind 入口 + @theme + base/utilities
libs/ui_design_system/      # 规划：基于 Base UI + Tailwind 的组件封装
```

### 12.2 Tailwind @theme 映射

所有 Design Tokens 定义在 `app/styles/app.css` 的 `@theme { }` 块中，
Tailwind 自动将其注册为 utility class 前缀（如 `bg-primary-900`、`text-text-secondary`）。

### 12.3 Typography Utility Classes

在 `@layer utilities` 中定义 10 个文本样式 class + 4 个状态色 class：

- `.text-title-page` / `.text-title-section` / `.text-title-card`
- `.text-data-primary` / `.text-data-secondary` / `.text-data-mono`
- `.text-body` / `.text-body-secondary`
- `.text-caption` / `.text-disclaimer`
- `.state-up` / `.state-down` / `.state-risk` / `.state-disabled`

---

## 13. 验收方式（BDD）

前端功能验收使用 Given/When/Then，输出格式遵循 `spec/BDD_TestSpec.md`。

### 验收检查清单

- [ ] 所有颜色来自 Design Token，无硬编码 hex
- [ ] 字重仅使用 400/500
- [ ] 圆角 ≤ 8px
- [ ] 阴影仅一层 `shadow-card`
- [ ] 红绿色仅用于数值标注
- [ ] 页面底部有免责声明
- [ ] 键盘可达、焦点可见
- [ ] 过渡动画 ≤ 120ms ease-out
