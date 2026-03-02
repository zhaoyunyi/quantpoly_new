## ADDED Requirements

### Requirement: UI components MUST be built on Base UI + Tailwind tokens

前端 UI 组件库 MUST 使用 Base UI（无头组件）与 Tailwind v4，并且全部视觉样式来自设计 tokens（`@theme` CSS variables）。

#### Scenario: No hard-coded colors in components
- **GIVEN** 工程师实现任意 UI 组件
- **WHEN** 检查样式定义
- **THEN** 不允许出现 `#RRGGBB`/`rgb()` 等硬编码颜色值
- **AND** 颜色必须来自 tokens（CSS variables 或 Tailwind token class）

### Requirement: Core components MUST define required interaction states

每个交互组件 MUST 覆盖 `default/hover/focus/disabled/loading/error` 状态，并满足可访问性要求（键盘可达、焦点可见）。

#### Scenario: Button supports keyboard focus ring
- **GIVEN** 用户使用键盘 Tab 导航
- **WHEN** 聚焦到 Button
- **THEN** 焦点环清晰可见

