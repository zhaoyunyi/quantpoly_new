## 1. `/strategies` 列表页

- [ ] 1.1 列表数据对接：`GET /strategies?page&pageSize&status&search`
- [ ] 1.2 搜索框（debounce）与筛选器（status/template）
- [ ] 1.3 分页组件（page/pageSize=20 对齐）
- [ ] 1.4 行操作：查看详情、编辑（跳转）、激活/停用、归档、删除
- [ ] 1.5 创建策略：
  - [ ] 从模板下拉选择（`GET /strategies/templates`）
  - [ ] 创建提交（`POST /strategies` 或 `POST /strategies/from-template`）
  - [ ] 失败分支：422 参数错误映射到字段
- [ ] 1.6 删除保护：
  - [ ] 二次确认 Dialog
  - [ ] 处理 409 `STRATEGY_IN_USE`

## 2. `/strategies/$id` 详情/编辑页

- [ ] 2.1 详情拉取：`GET /strategies/{id}`
- [ ] 2.2 编辑保存：`PUT /strategies/{id}`（仅允许 name/parameters 等）
- [ ] 2.3 状态变更：
  - [ ] `POST /strategies/{id}/activate`
  - [ ] `POST /strategies/{id}/deactivate`
  - [ ] `POST /strategies/{id}/archive`
- [ ] 2.4 关联回测：
  - [ ] 列表：`GET /strategies/{id}/backtests`
  - [ ] 统计：`GET /strategies/{id}/backtest-stats`
  - [ ] 快捷创建回测：`POST /strategies/{id}/backtests`（或跳转到 backtests 创建）
- [ ] 2.5 执行参数校验：`POST /strategies/{id}/validate-execution`

## 3. `/strategies/simple` 向导创建

- [ ] 3.1 Step1：模板选择（`GET /strategies/templates`）
- [ ] 3.2 Step2：关键参数输入（按 template 驱动字段）
- [ ] 3.3 Step3：确认预览 + 创建提交（`POST /strategies/from-template`）
- [ ] 3.4 创建后可选“立即回测”：
  - [ ] `POST /strategies/{id}/backtests`（默认 config）
  - [ ] 成功后跳转 `/backtests/$id` 或策略详情

## 4. `/strategies/compare` 对比

- [ ] 4.1 选择 2-5 个策略
- [ ] 4.2 为每个策略选取对比用 backtest（默认：最新 completed；允许手动选择）
- [ ] 4.3 调用 `POST /backtests/compare`（taskIds）并展示对比表
- [ ] 4.4 导出（CSV 先行，PDF 可后置）

## 5. `/strategies/advanced` 高级入口

- [ ] 5.1 作为高级分析目录页（对比、研究任务入口）
- [ ] 5.2 研究任务：
  - [ ] `POST /strategies/{id}/research/performance-task`
  - [ ] `POST /strategies/{id}/research/optimization-task`
  - [ ] `GET /strategies/{id}/research/results`

## 6. 组件规划（可并行）

- [ ] 6.1 `StrategyTable`（Table + RowActions + EmptyState）
- [ ] 6.2 `StrategyForm`（字段 schema 驱动；支持 readonly/edit）
- [ ] 6.3 `TemplateSelect`（加载态/失败重试）
- [ ] 6.4 `StrategyStatusBadge`
- [ ] 6.5 `BacktestInlineList`（策略详情内嵌）
- [ ] 6.6 `CompareMatrix`（对比表 + 可选图表）
- [ ] 6.7 `WizardStepper`（simple 模式）

## 7. 测试（TDD）

- [ ] 7.1 单元测试：列表页筛选/分页参数正确传递
- [ ] 7.2 单元测试：删除 409 显示“回测占用”提示
- [ ] 7.3 单元测试：simple 向导完整走通（mock API）

## 8. 回归验证

- [ ] 8.1 `cd apps/frontend_web && npm run build`
- [ ] 8.2 `pytest -q`

