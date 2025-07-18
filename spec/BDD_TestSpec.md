# BDD 测试规范指南：面向 AI Agent (结构化输出版)

## 1. 概述 (Overview)
本规范指导 AI Agent 执行 BDD 测试，并要求输出符合**层级化、蛇形命名**风格的测试报告（类似 Go Testing 输出）。

## 2. 核心三段式规范 (Logic Specification)

### 🔴 Given (前置) -> 🟢 When (动作) -> 🔵 Then (断言)
*(逻辑执行部分与之前保持一致，重点在于如何描述这些步骤)*

---

## 3. 关键：命名与输出规范 (Naming & Output Standards) 🔥 重要修改

为了生成符合标准格式的测试结果，AI Agent 必须严格遵守以下文本转换规则。

### 3.1 命名转换规则 (Naming Conversion)
AI 在生成日志或报告时，必须将自然语言描述转换为**蛇形命名法 (Snake Case)**：
1.  **空格替换**：将所有空格替换为下划线 `_`。
2.  **变量标记**：涉及具体参数值时，使用 `$` 前缀（例如 `$high`, `$true`）。
3.  **保留中文**：不强制翻译英文，保持语义准确。

> **转换示例**：
> *   原文："当 thinkingEffort 为 high 时"
> *   转换后：`当_thinkingEffort=$high_时`
>
> *   原文："应该生成一条计费记录"
> *   转换后：`应该生成一条计费记录`

### 3.2 层级结构定义 (Hierarchy Definition)
输出必须严格遵循 `测试类/场景/步骤` 的三级路径格式：

*   **Level 1: 测试套件 (Test Suite)**
    *   命名格式：`Test[功能模块名]` (帕斯卡命名法)
    *   例如：`TestClaudeServerSearch`, `TestClaude思考级别控制`
*   **Level 2: 场景 (Scenario)**
    *   命名格式：`场景: [场景描述]` (蛇形命名)
    *   例如：`场景: 使用_server_search_工具`
*   **Level 3: 步骤 (Step - When/Then)**
    *   命名格式：`[关键字]_[描述]`
    *   例如：`当请求成功时`, `应该有非空的_RequestID`

---

## 4. AI Agent 执行 Prompt 模板

请使用以下 Prompt 驱动 AI，以确保输出与截图完全一致：

```text
你是一个遵循严格日志规范的测试 Agent。
请执行以下测试场景，并按指定格式输出每一行测试结果。

【格式要求】
1. 每一行输出代表一个测试节点的完成。
2. 必须使用 "/" 分隔层级：TestSuite / Scenario / Step。
3. 描述部分必须使用下划线连接 (snake_case)。
4. 成功输出 "✅ " 前缀，失败输出 "❌ " 前缀。

【输入场景】
Feature: Claude Server Search
Scenario: 使用 server search 工具
  When: 请求成功时
  Then: 应该生成一条计费记录
  Then: 应该包含 server_search 计费项
  Then: 应该正确计算总费用

【期望你的输出格式示例】
✅ TestClaudeServerSearch/场景: 使用_server_search_工具/当请求成功时
✅ TestClaudeServerSearch/场景: 使用_server_search_工具/当请求成功时/应该生成一条计费记录
✅ TestClaudeServerSearch/场景: 使用_server_search_工具/当请求成功时/应该包含_server_search_计费项