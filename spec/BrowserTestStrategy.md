# 浏览器测试策略规范：Playwright vs AI 驱动浏览器代理

> **版本**：1.0 · **更新日期**：2026-04-18
>
> 本规范定义在 QuantPoly 项目中，何时使用 **Playwright**（确定性浏览器自动化），何时使用 **AI 驱动浏览器代理**（例如 Browser Use 或具备真实浏览器能力的代理工具），以及两者的判断标准、适用场景和反模式。

---

## 1. 概述

### 1.1 工具定位

| 工具 | 本质 | 核心能力 | 执行模式 |
|------|------|---------|---------|
| **Playwright** | 确定性浏览器自动化框架 | 精确控制浏览器行为，通过 selector 和网络拦截做稳定断言 | 脚本驱动，结果可重复 |
| **AI 驱动浏览器代理** | LLM 驱动的浏览器代理 | 通过页面语义和自然语言目标完成巡检、验收、语义判断 | 推理驱动，结果具概率性 |

### 1.2 项目现状

- 当前仓库已经内置 **Playwright E2E**，入口命令为 `cd apps/frontend_web && npm run test:e2e`。
- 当前仓库前端 E2E 通过 `apps/frontend_web/playwright.config.ts` 启动前端和一个 **内存态后端**，适合做稳定的端到端回归。
- 当前仓库**尚未内置** AI 浏览器代理脚本；如后续引入，只能作为 **非阻断、非 CI Gate** 的补充验证层。

### 1.3 决策原则

> **默认选 Playwright。只有当 Playwright 的维护成本明显高于 AI 浏览器代理的不确定性成本时，才考虑 AI 浏览器代理。**

---

## 2. 判断决策树

```text
需要浏览器测试？
  │
  ├─ 是否进入 CI / 门禁链路？
  │   └─ 是 → ✅ Playwright
  │
  ├─ 是否需要稳定断言 URL、文本、状态、表格、图表或跳转逻辑？
  │   └─ 是 → ✅ Playwright
  │
  ├─ 是否需要通过 webServer / 内存后端隔离状态？
  │   └─ 是 → ✅ Playwright
  │
  ├─ 是否需要拦截网络或精确控制测试数据？
  │   └─ 是 → ✅ Playwright
  │
  ├─ 是否是部署后一次性 Smoke / 人工验收替代？
  │   └─ 是 → 🤖 AI 驱动浏览器代理
  │
  ├─ 是否需要回答“页面看起来是否正常”“流程是否走通”这类语义问题？
  │   └─ 是 → 🤖 AI 驱动浏览器代理
  │
  ├─ 是否涉及第三方页面或难维护 selector 的跨站流程？
  │   └─ 是 → 🤖 AI 驱动浏览器代理
  │
  └─ 默认 → ✅ Playwright
```

---

## 3. Playwright 适用场景

### 3.1 核心标准

满足以下任意一条即应选用 Playwright：

1. **确定性要求高**：测试结果必须稳定可重复。
2. **CI Gate**：测试作为质量门，失败即阻断合并、发布或回归通过。
3. **需要状态隔离**：依赖 `playwright.config.ts` 启动的独立前后端进程和内存态后端。
4. **需要精确断言**：验证具体文本、属性、路由、接口副作用、图表渲染、鉴权跳转。
5. **高频执行**：每次提交或每次回归都要跑，不能接受长时间 LLM 推理。

### 3.2 本项目中的 Playwright 覆盖范围

当前仓库中，以下测试天然属于 Playwright 范畴：

| 测试文件 | 覆盖范围 | 为什么是 Playwright |
|---------|---------|-------------------|
| `apps/frontend_web/tests/e2e/auth-dashboard.spec.ts` | 登录与仪表盘链路 | 需要稳定验证鉴权与页面跳转 |
| `apps/frontend_web/tests/e2e/backtests.spec.ts` | 回测页面流程 | 需要稳定验证状态与表单流 |
| `apps/frontend_web/tests/e2e/monitor.spec.ts` | 实时监控页面 | 需要稳定验证数据展示与页面交互 |
| `apps/frontend_web/tests/e2e/strategies.spec.ts` | 策略管理流程 | 需要稳定验证列表、详情与操作结果 |
| `apps/frontend_web/tests/e2e/trading.spec.ts` | 交易页面流程 | 需要稳定验证下单/风险链路的前端行为 |

### 3.3 Playwright 编写规范

```ts
// ✅ 正确：稳定定位 + 稳定断言
await page.goto('/dashboard')
await expect(page.getByRole('heading', { name: /仪表盘/i })).toBeVisible()

// ✅ 正确：依赖 webServer 启动的可重复环境
// 参见 apps/frontend_web/playwright.config.ts

// ❌ 错误：把“页面看起来是否舒服”这种语义判断写成 Playwright 主断言
// ❌ 错误：把部署后一次性人工巡检放进 CI Gate
```

---

## 4. AI 驱动浏览器代理适用场景

### 4.1 核心标准

满足以下全部条件时，才考虑 AI 驱动浏览器代理：

1. **非 CI Gate**：失败不会阻断主流程。
2. **语义判断为主**：例如“页面是否正常渲染”“内容层级是否完整”“部署后入口是否可用”。
3. **维护 selector 成本高**：流程涉及第三方站点、动态结构或一次性验收页面。
4. **执行频率低**：适合部署后 Smoke、验收巡检、人工验证替代，而不是每次提交都跑。

### 4.2 在 QuantPoly 中适用的典型场景

- 部署后首页、登录页、仪表盘入口是否“整体可用”的语义巡检。
- 第三方登录授权页、外部跳转页、需要人工观察的跨站流程探测。
- 面向产品或运维的“发布后 Smoke”任务，重点是页面可达、关键 CTA 可见、主流程未断。
- 需要同时判断布局、视觉层级、文案缺失等 Playwright 不擅长的语义问题。

### 4.3 当前项目约束

- 当前仓库**没有**现成的 AI 浏览器代理测试目录、脚本或门禁接入。
- 如果未来引入，必须放在 **部署后验收层**，而不是替换现有 Playwright E2E。
- 如果未来引入，建议单独落在 `scripts/` 或 `tests/browser_agent/`，并明确标记为 **non-blocking**。

---

## 5. 反模式（禁止事项）

### 5.1 禁止用 AI 浏览器代理替换现有 Playwright E2E

```text
❌ “这个 Playwright 测试写起来麻烦，全部改成 AI 浏览器代理吧”
✅ “现有稳定 E2E 保持 Playwright，只把一次性语义巡检留给 AI 浏览器代理”
```

### 5.2 禁止在 CI Gate 中使用 AI 浏览器代理

```text
❌ CI: npm run test:browser-agent
✅ CI: npm run test && npm run test:e2e
✅ 部署后: 运行 AI 浏览器代理 smoke（允许告警，不阻断）
```

### 5.3 禁止用浏览器代理替代后端 API / CLI 测试

```text
❌ 用浏览器代理验证 capability gate / storage contract gate
✅ 直接运行 CLI、pytest、Playwright 或 shell 脚本
```

### 5.4 禁止为了使用 AI 浏览器代理而拆掉现有自动化

```text
❌ 删除现有 Playwright 与 pytest，只保留“像人一样点页面”
✅ 保留原有自动化，把 AI 浏览器代理作为补充验收层
```

---

## 6. 技术选型对比表

| 维度 | Playwright | AI 驱动浏览器代理 |
|------|-----------|-------------------|
| **执行速度** | 快（秒级） | 慢（分钟级，含推理） |
| **确定性** | 高，可重复 | 概率性 |
| **API 成本** | 零 | 依赖模型调用成本 |
| **维护成本** | 中（selector 变更需维护） | 中低（自然语言更抗结构变化） |
| **网络拦截 / Mock** | 强 | 弱或无 |
| **语义判断** | 弱 | 强 |
| **CI 适用性** | 强 | 弱 |
| **第三方页面适配** | 一般 | 较强 |
| **调试体验** | 强（trace / screenshot / video） | 依赖日志、录屏与模型输出 |

---

## 7. 项目中的执行位置

```text
代码提交
  ↓
Stage 1: 单元 / 组件测试（Vitest）
  ↓
Stage 2: Playwright E2E（apps/frontend_web/tests/e2e）
  ↓
Stage 3: 后端冒烟 / 门禁脚本（pytest / shell / CLI）
  ↓
Stage 4: 可选的部署后 AI 浏览器验收
  ↓
验收完成
```

关键约束：

- **Stage 2 必须稳定且可重复**。
- **Stage 4 只能补充，不得替代前面阶段**。
- AI 浏览器验收失败默认应视为 **告警或人工复核信号**，而不是自动阻断。

---

## 8. 与本仓库其他规范的关系

- 与 `spec/BDD_TestSpec.md` 配合：定义输出与场景表达格式。
- 与 `spec/UISpec.md` 配合：决定前端页面应如何被断言、巡检和验收。
- 与 `apps/frontend_web/playwright.config.ts` 配合：以项目内实际 E2E 启动方式为准。

---

## 9. 变更历史

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-04-18 | 初版：基于外部新版测试策略结构，按 QuantPoly 适配落地 | Codex |
