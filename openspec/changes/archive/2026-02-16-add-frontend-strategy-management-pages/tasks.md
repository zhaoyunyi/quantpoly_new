## 1. `/strategies` 列表页

- [x] 1.1 列表数据对接：`GET /strategies?page&pageSize&status&search`
- [x] 1.2 搜索框（debounce）与筛选器（status/template）
- [x] 1.3 分页组件（page/pageSize=20 对齐）
- [x] 1.4 行操作：查看详情、编辑（跳转）、激活/停用、归档、删除
- [x] 1.5 创建策略：
  - [x] 从模板下拉选择（`GET /strategies/templates`）
  - [x] 创建提交（`POST /strategies` 或 `POST /strategies/from-template`）
  - [x] 失败分支：422 参数错误映射到字段
- [x] 1.6 删除保护：
  - [x] 二次确认 Dialog
  - [x] 处理 409 `STRATEGY_IN_USE`

## 2. `/strategies/$id` 详情/编辑页

- [x] 2.1 详情拉取：`GET /strategies/{id}`
- [x] 2.2 编辑保存：`PUT /strategies/{id}`（仅允许 name/parameters 等）
- [x] 2.3 状态变更：
  - [x] `POST /strategies/{id}/activate`
  - [x] `POST /strategies/{id}/deactivate`
  - [x] `POST /strategies/{id}/archive`
- [x] 2.4 关联回测：
  - [x] 列表：`GET /strategies/{id}/backtests`
  - [x] 统计：`GET /strategies/{id}/backtest-stats`
  - [x] 快捷创建回测：`POST /strategies/{id}/backtests`（或跳转到 backtests 创建）
- [x] 2.5 执行参数校验：`POST /strategies/{id}/validate-execution`

## 3. `/strategies/simple` 向导创建

- [x] 3.1 Step1：模板选择（`GET /strategies/templates`）
- [x] 3.2 Step2：关键参数输入（按 template 驱动字段）
- [x] 3.3 Step3：确认预览 + 创建提交（`POST /strategies/from-template`）
- [x] 3.4 创建后可选“立即回测”：
  - [x] `POST /strategies/{id}/backtests`（默认 config）
  - [x] 成功后跳转 `/backtests/$id` 或策略详情

## 4. `/strategies/compare` 对比

- [x] 4.1 选择 2-5 个策略
- [x] 4.2 为每个策略选取对比用 backtest（默认：最新 completed；允许手动选择）
- [x] 4.3 调用 `POST /backtests/compare`（taskIds）并展示对比表
- [x] 4.4 导出（CSV 先行，PDF 可后置）

## 5. `/strategies/advanced` 高级入口

- [x] 5.1 作为高级分析目录页（对比、研究任务入口）
- [x] 5.2 研究任务：
  - [x] `POST /strategies/{id}/research/performance-task`
  - [x] `POST /strategies/{id}/research/optimization-task`
  - [x] `GET /strategies/{id}/research/results`

## 6. 组件规划（可并行）

- [x] 6.1 `StrategyTable`（Table + RowActions + EmptyState）
- [x] 6.2 `StrategyForm`（字段 schema 驱动；支持 readonly/edit）
- [x] 6.3 `TemplateSelect`（加载态/失败重试）
- [x] 6.4 `StrategyStatusBadge`
- [x] 6.5 `BacktestInlineList`（策略详情内嵌）
- [x] 6.6 `CompareMatrix`（对比表 + 可选图表）
- [x] 6.7 `WizardStepper`（simple 模式）

## 7. 测试（TDD）

- [x] 7.1 单元测试：列表页筛选/分页参数正确传递
- [x] 7.2 单元测试：删除 409 显示“回测占用”提示
- [x] 7.3 单元测试：simple 向导完整走通（mock API）

## 8. 回归验证

- [x] 8.1 `cd apps/frontend_web && npm run build`
- [x] 8.2 `pytest -q`

