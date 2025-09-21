# 2026-02-11 Wave6 剩余后端功能迁移盘点与拆分

## 1. 盘点目标与输入

- 目标：在 Wave5 全量归档后，继续识别“旧项目已有/产品愿景要求，但当前后端仍未完全闭环”的能力缺口，并按依赖关系拆分为下一批 OpenSpec。
- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 关键输入：
  - 旧项目路由：`quantpoly-backend/backend/app/api/routes/*.py`
  - 当前路由：`libs/*/*/api.py`、`libs/user_auth/user_auth/app.py`、`apps/backend_app/router_registry.py`
  - 愿景与需求：`docs/需求分析最终版本.md`、`docs/specs/mvp-spec.md`、`docs/项目总体架构设计.md`（源项目）
  - 规范约束：`spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`

## 2. 对齐结论（Wave5 后）

## 2.1 已完成主干能力迁移

以下域能力已形成后端聚合闭环，且多数场景已具备 API + Library + CLI + 测试：

- 用户认证与用户治理（`user-auth` + `user-preferences`）
- 策略管理 / 回测 / 交易账户 / 风控 / 信号执行
- 市场数据查询、指标任务入口、风险与交易自动化任务入口
- 组合入口统一鉴权、统一错误 envelope、统一脱敏日志

## 2.2 路径 break 但功能可视为已覆盖

以下属于“路径命名收口差异”，非功能缺失：

- `/risk-control/*` 收口为 `/risk/*`
- `/strategy-execution/*` 收口到 `/signals/* + /strategies/*`
- `/monitoring/summary` 收口为 `/monitor/summary`
- `/users/*` 管理动作收口为 `/admin/users/*`

## 2.3 仍存在的功能/架构缺口（需要 Wave6）

### P0-1 用户找回流程生产化不足（安全与可恢复性）

现状证据：

- `libs/user_auth/user_auth/app.py:18` 使用 `InMemoryPasswordResetStore`
- `libs/user_auth/user_auth/app.py:240` 在 request 接口直接返回 `resetToken`

缺口：

1. 重置 token 未持久化，服务重启后流程不可恢复；
2. token 直接返回调用方，不满足生产安全边界；
3. 缺少统一的密码找回审计与频控语义。

风险：

- 账号接管与枚举风险提升；
- 运维不可追踪密码找回链路；
- 与“用户系统后端托管”目标不完全一致（仅完成了功能，不满足生产化治理深度）。

### P0-2 监控摘要与运营视图语义不完整

现状证据：

- `libs/monitoring_realtime/monitoring_realtime/app.py:184-185` 任务摘要固定 `running=0`

缺口：

1. 监控摘要未覆盖旧系统核心运营字段（账户覆盖、活跃策略、运行中回测/任务）；
2. WebSocket 与 REST 的“运营级指标”一致性不足（目前偏信号/告警计数）。

风险：

- 监控首屏无法准确反映系统运行态；
- 排障需要跨域手工拼装数据，违背后端读模型收口目标。

### P1-1 市场数据真实 Provider 仍未可运行装配

现状证据：

- `apps/backend_app/router_registry.py:100-101` 默认 alpaca transport 直接抛错
- `libs/market_data/market_data/cli.py:15-16` CLI 默认 transport 也是未配置占位

缺口：

1. 运行时虽支持 `market_data_provider=alpaca` 配置，但无可用 transport 实现；
2. CLI 无法在真实 provider 下运行，偏离 CLI Mandate 的“可观测可验证”要求。

风险：

- 上线后配置为 alpaca 会在运行时失败；
- 行情链路真实性不足，影响回测/交易/风控可信度。

### P1-2 任务编排仅有状态机，缺少可持续执行器语义

现状证据：

- `libs/job_orchestration/job_orchestration/scheduler.py` 为纯 `InMemoryScheduler`
- 调度仅注册/停止，不具备持久恢复与实际执行派发语义

缺口：

1. 缺乏统一 worker/executor 抽象与落地（至少本地 runtime 实现）；
2. 调度配置与执行状态缺少“重启可恢复”链路。

风险：

- 长任务自动化行为受限于单进程内存生命周期；
- “异步任务编排”能力在生产约束下不稳定。

### P2-1 策略研究能力仍偏占位，未达到愿景深度

现状（产品愿景对照）：

- 愿景文档强调“参数优化系统（网格/贝叶斯）+ 结果可视化 + 市场环境分析”；
- 当前策略研究自动化已具入口，但优化结果与研究读模型仍偏轻量。

缺口：

1. 缺少可复算、可追溯的研究结果聚合与读模型；
2. 缺少与市场数据指标体系联动的参数搜索闭环。

风险：

- 与“进阶用户策略优化”价值主张存在落差；
- 难以支撑后续策略推荐与自动化研究演进。

## 3. 架构合理性审查与调整建议

## 3.1 当前合理点（保持）

- 限界上下文拆分较清晰，核心域已 library-first；
- API 错误 envelope、ACL、日志脱敏方向正确；
- OpenSpec → 实现 → 归档流程执行稳定。

## 3.2 建议调整点（Wave6 聚焦）

1. **认证恢复链路生产化**：重置 token 改为持久化 + 哈希化存储 + 审计事件；
2. **监控读模型运营化**：补齐 monitor summary 的账户/策略/回测/任务指标并统一口径；
3. **Provider 真装配**：在组合入口与 CLI 注入真实 alpaca transport（支持 fail-fast 与健康检查）；
4. **任务执行器基线**：在 job orchestration 增加 executor 抽象与持久化调度恢复。

## 4. Wave6 OpenSpec 拆分（按依赖/可并行）

## 4.1 串行基座（先做）

1. `update-job-orchestration-runtime-executor-baseline`
   - 目标：补齐任务执行器抽象、调度恢复语义、任务状态与执行日志关联。
   - 影响 spec：`job-orchestration`（必要时联动 `platform-core`）。

## 4.2 可并行包 A（与基座弱依赖）

2. `update-user-auth-password-recovery-hardening`
   - 目标：找回 token 持久化、响应脱敏、审计与频控语义。
   - 影响 spec：`user-auth`。

3. `update-market-data-alpaca-live-transport`
   - 目标：实现运行时/CLI 的 alpaca transport 注入、配置校验与健康探针。
   - 影响 spec：`market-data`。

## 4.3 可并行包 B（依赖基座）

4. `update-monitoring-summary-operational-parity`
   - 目标：监控摘要补齐运行态指标（账户、策略、回测、任务）并与 WS 语义一致。
   - 依赖：`update-job-orchestration-runtime-executor-baseline`（任务统计口径）。
   - 影响 spec：`monitoring-realtime`。

5. `update-strategy-research-optimization-depth`
   - 目标：补齐策略研究结果聚合/读模型，增强参数优化闭环（可 break 旧轻量语义）。
   - 依赖：`update-job-orchestration-runtime-executor-baseline`、`update-market-data-alpaca-live-transport`。
   - 影响 spec：`strategy-management`、`market-data`（如需指标依赖声明）。

## 5. 依赖图（串并行）

- 串行第一步：`update-job-orchestration-runtime-executor-baseline`
- 并行可立即做：`update-user-auth-password-recovery-hardening`、`update-market-data-alpaca-live-transport`
- 基座后并行：`update-monitoring-summary-operational-parity`、`update-strategy-research-optimization-depth`

可视化：

```text
update-job-orchestration-runtime-executor-baseline
    ├── update-monitoring-summary-operational-parity
    └── update-strategy-research-optimization-depth

update-user-auth-password-recovery-hardening  (independent)
update-market-data-alpaca-live-transport      (independent, but strategy-research可复用)
```

## 6. 实施与验收约束（延续）

1. **Library-First**：先补库能力（domain/service/repository），再挂 API；
2. **CLI Mandate**：新增能力必须同步 CLI 子命令或参数；
3. **Test-First**：严格 RED → GREEN；
4. **DDD**：跨上下文通过 ACL/读模型，不跨域直连内部仓储；
5. **BDD**：关键场景 Given/When/Then + snake_case 输出。

## 7. 结论

Wave5 后已完成“主干迁移”；Wave6 重点从“功能存在”转向“生产可运行 + 运营可观测 + 研究可扩展”。

建议下一步按上述 5 个 change-id 创建 OpenSpec proposal/tasks/spec deltas，并先评审再进入实现。
