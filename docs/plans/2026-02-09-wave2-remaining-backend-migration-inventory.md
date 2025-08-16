# 2026-02-09 Wave2 剩余后端功能迁移盘点（源项目 → 当前仓库）

## 1. 目标与范围

- 目标：在“允许 break、但功能不缺失”的约束下，完成源项目剩余后端能力迁移拆分。
- 范围：
  - 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend/app`
  - 目标项目：当前仓库 `libs/*`、`apps/backend_app/*`、`openspec/*`
- 本文聚焦三件事：
  1. 识别剩余能力缺口；
  2. 判断依赖关系与可并行迁移面；
  3. 输出可执行 OpenSpec 拆分。

## 2. 产品愿景对齐结论（需求/架构文档）

结合源项目文档：

- `docs/需求分析最终版本.md`
- `docs/技术架构详细设计文档.md`

当前产品核心闭环仍是：

1. 策略研究闭环：策略管理 → 回测 → 分析对比；
2. 模拟交易闭环：账户/订单/成交/资金流水 → 风险评估 → 监控；
3. 治理闭环：用户分层（Level）+ 管理员动作审计；
4. 数据闭环：行情检索/历史/批量报价 + 实时监控一致口径。

结论：当前仓库已完成 Wave1 主能力，但在“闭环深度”上仍有缺口，主要体现在：

- 策略与回测的联动读模型不足；
- 交易账户生命周期与风险评估读模型未补齐；
- 信号中心观测面（详情/过期/仪表板）不完整；
- 长任务编排与领域任务桥接未收口。

## 3. 剩余差距矩阵（按限界上下文）

| 限界上下文 | 已完成 | 仍需迁移/重构 | 优先级 |
|---|---|---|---|
| user-auth / admin-governance | 用户生命周期、管理员治理、审计已具备 | 管理员权限判定语义统一（`role/level` 与 `is_admin` 收口） | P0 |
| strategy-management + backtest-runner | 模板化创建、状态机、回测任务基础能力 | 策略更新、策略发起回测、策略维度回测列表/统计、回测删除闭环 | P1 |
| trading-account + risk-control | 订单账本、交易分析、价格刷新、待处理订单 | 账户创建/更新/详情、过滤配置、账户摘要与现金流摘要、风险评估快照/evaluate | P1 |
| signal-execution + monitoring-realtime | 批处理、执行记录、趋势、维护接口 | 信号详情、过期迁移、pending/expired/filter/search、账户仪表板与统计口径统一 | P1 |
| job-orchestration | 幂等任务模型与调度骨架 | 回测/信号/风控/交易任务桥接，统一 taskId 语义与状态追踪 | P2 |

## 4. 已识别的设计缺陷/潜在 Bug

### 4.1 管理员判定存在语义漂移（高优先级）

当前业务路由多处使用：

- `bool(getattr(current_user, "is_admin", False))`

而 `user_auth.domain.User` 聚合根实际以 `role`/`level` 表达治理属性，未提供 `is_admin` 字段。会导致“管理员用户在部分高风险接口被误判为普通用户”。

建议：统一管理员判定入口（平台层 helper），禁止业务路由直接读取裸字段。

### 4.2 策略研究链路存在“孤岛任务”风险

当前回测虽可提交，但策略域对“该策略历史回测/统计”缺少一等读模型，会削弱产品的策略研究闭环。

### 4.3 交易账户生命周期未闭环

当前以订单与分析能力为主，账户实体生命周期接口（create/get/update/filter-config）未完整暴露，不利于前端收敛为纯 API 调用。

## 5. 依赖与并行拆分建议

### 5.1 执行顺序（建议）

- **Phase 0（串行）**：`update-admin-role-resolution-parity`
- **Phase 1（并行）**：
  - `update-strategy-backtest-linkage-parity`
  - `update-trading-account-lifecycle-risk-parity`
  - `update-signal-center-readmodel-parity`
- **Phase 2（串行收口）**：`update-job-orchestration-domain-task-parity`

### 5.2 并行性判断

- Phase 1 三项互相依赖较低，可并行推进；
- Phase 2 依赖 Phase 1 的领域动作稳定后再统一接入任务编排，避免接口语义回滚。

## 6. 架构调整建议（对齐 ProgramSpec / DDDSpec）

1. **Library-First 强化**：
   - 每个新增能力先落库（service/repository/domain），再暴露 API 与 CLI；
   - 禁止在 `apps/backend_app` 写业务规则。
2. **聚合边界强化**：
   - `strategy-management` 聚焦策略聚合与约束；
   - `backtest-runner` 仅承载回测任务与结果聚合；
   - 两者通过 ACL（按 `strategy_id` + `user_id`）联动。
3. **治理语义统一**：
   - 管理员与等级判定从业务上下文抽到平台层统一策略；
   - 所有高风险动作走 `admin-governance` 审计。
4. **任务编排统一**：
   - 统一 taskId / idempotencyKey 语义；
   - 统一状态机与错误码（冲突/越权/不可迁移）。

## 7. 本轮拆分产物

本轮已创建 5 个 OpenSpec 变更用于后续迁移实施：

1. `update-admin-role-resolution-parity`
2. `update-strategy-backtest-linkage-parity`
3. `update-trading-account-lifecycle-risk-parity`
4. `update-signal-center-readmodel-parity`
5. `update-job-orchestration-domain-task-parity`

