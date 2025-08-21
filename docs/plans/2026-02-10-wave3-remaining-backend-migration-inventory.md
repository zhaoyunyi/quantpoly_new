# 2026-02-10 Wave3 剩余后端功能迁移盘点（归档后下一阶段）

## 1. 背景

在以下变更归档完成后：

- `update-admin-role-resolution-parity`
- `update-strategy-backtest-linkage-parity`
- `update-trading-account-lifecycle-risk-parity`
- `update-signal-center-readmodel-parity`
- `update-job-orchestration-domain-task-parity`

当前仓库已完成用户系统后端聚合与核心业务上下文骨架，但与源项目后端相比，仍有“自动化任务与研究分析深度”缺口。

## 2. 盘点结论（源项目 vs 当前项目）

### 2.1 路由层

源项目 `strategy_execution.py` 仍存在以下能力语义需要补齐/收口：

- 策略驱动信号生成与处理的完整闭环（`signals/generate`、`signals/{id}/process`）
- 执行记录生命周期维护（运行中视图、按周期趋势、历史清理）

### 2.2 Worker 任务层（核心缺口）

源项目存在 22 个领域任务（`worker/tasks/*.py`），而当前 `job-orchestration` 仅覆盖 6 个 task type。
主要差距集中在：

1. 策略研究自动化：批量执行、绩效分析、优化建议、策略回测任务化。
2. 信号分析自动化：批量生成/处理、绩效分析、洞察生成、过期清理策略。
3. 风控运营自动化：批量巡检、风险报告、告警通知、连续监控、快照批处理。
4. 交易运营自动化：待处理交易、日统计、风险巡检、批量执行、账户清理。
5. 行情数据管道：数据同步、技术指标计算、同步一致性校验。

## 3. 产品愿景对齐分析

结合源项目需求文档与总体架构文档（`docs/需求分析最终版本.md`、`docs/项目实施计划文档.md`、`docs/技术架构详细设计文档.md`），产品愿景不仅是 CRUD 能力齐全，更要求：

- Level 2 用户具备策略研究深度（绩效分析、优化建议、策略对比）。
- 模拟交易具备运营闭环（批处理、日统计、风险联动、清理维护）。
- 风控与监控具备持续化与通知能力（而非仅查询接口）。

结论：当前仓库已满足“主干业务可用”，但尚未满足“研究与运营自动化深度”。

## 4. 架构合理性与潜在缺陷

### 4.1 合理点

- 已实现 bounded context 拆分，符合 DDD 边界。
- 用户系统后端聚合已完成，符合 hard-cutover 目标。
- `job-orchestration` 已建立统一任务状态机与幂等基础。

### 4.2 需调整点 / 潜在缺陷

1. **任务类型覆盖不足**：无法承载源项目多数后台自动化任务。
2. **调度语义未充分租户化**：调度层缺少“用户范围 + 任务命名空间”统一规则，存在语义漂移风险。
3. **执行历史清理策略不完整**：信号/执行清理缺少统一保留策略与审计语义。
4. **研究能力缺口**：策略优化建议、信号洞察等能力尚未进入当前后端模型。

## 5. 依赖与并行拆分建议（Wave3）

### 5.1 P0 基座（串行）

- `update-job-orchestration-worker-task-coverage`

目标：先把任务编排从“6 个任务类型”扩展为“可注册、可查询、可审计”的领域任务底座。

### 5.2 P1 并行域迁移（并行）

1. `update-strategy-signal-automation-parity`
2. `update-risk-reporting-automation-parity`
3. `update-trading-operations-automation-parity`
4. `update-market-data-pipeline-automation-parity`

说明：上述 4 项可并行推进，但统一依赖 P0 的任务类型覆盖与调度语义。

### 5.3 P2 收口（串行）

- 统一回归与能力门禁（能力矩阵 + GWT 场景 + CLI gate）。

## 6. 本轮产出

本轮已创建 5 个 OpenSpec 提案（1 串行 + 4 并行），用于进入 Wave3 执行阶段。

## 7. 验收要求（延续）

- 遵循 `spec/ProgramSpec.md`：Library-First / CLI Mandate / Test-First。
- 遵循 `spec/DDDSpec.md`：跨上下文通过 ACL/OHS，不做跨域直连。
- 遵循 `spec/BDD_TestSpec.md`：Given/When/Then 场景与 snake_case 测试输出。
