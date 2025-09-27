# 2026-02-12 Wave7 剩余后端功能迁移盘点与拆分

## 1. 盘点范围与方法

- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 盘点输入：
  - 源路由与任务系统：`app/api/routes/*.py`、`app/worker/celery_app.py`、`app/worker/tasks/*.py`
  - 源需求与愿景：`docs/需求分析最终版本.md`、`docs/技术架构详细设计文档.md`
  - 当前后端实现：`libs/*/*/api.py`、`libs/job_orchestration/*`、`apps/backend_app/router_registry.py`

本轮以“功能是否缺失 + 架构是否满足长期愿景”双维度审查。

## 2. 当前结论（Wave6 归档后）

## 2.1 已完成能力

- Wave6 的 5 个变更已实现并归档：
  - `update-job-orchestration-runtime-executor-baseline`
  - `update-user-auth-password-recovery-hardening`
  - `update-market-data-alpaca-live-transport`
  - `update-monitoring-summary-operational-parity`
  - `update-strategy-research-optimization-depth`
- `openspec validate --specs --strict` 已全通过。

## 2.2 剩余迁移缺口（本轮识别）

### P0-1 任务编排“真实派发链路”尚未贯通

现状证据：

- `dispatch_job` 仅在 `job_orchestration` 自测中出现：
  - `libs/job_orchestration/job_orchestration/service.py`
  - `libs/job_orchestration/tests/test_runtime_executor.py`
- 业务域 API 基本采用“submit → start → succeed 即时完成”模式：
  - 例：`libs/risk_control/risk_control/api.py`
  - 例：`libs/trading_account/trading_account/api.py`
  - 例：`libs/strategy_management/strategy_management/api.py`

对照源项目：

- 源项目存在 Celery + Redis + Beat 的任务运行时与队列路由：
  - `quantpoly-backend/backend/app/worker/celery_app.py`

风险：

1. 任务“异步语义”名实不符，长任务/失败恢复能力受限；
2. 任务状态观测（queued/running/failed）缺少真实调度支撑；
3. 难以平滑接入生产 worker 与调度策略。

### P1-1 市场实时流网关缺失（仅有 REST 拉取）

现状证据：

- 当前 `market-data` 无 `stream` 类 API/WS 入口；
- 当前监控实时能力集中在 `monitoring_realtime`，但市场行情推流未收口到 `market-data` 领域。

对照源愿景：

- 技术架构文档明确了实时行情 WebSocket 与 `WS /api/market/stream` 目标：
  - `docs/技术架构详细设计文档.md`

风险：

1. 市场数据只能轮询，实时策略与监控延迟不可控；
2. 前后端流式订阅协议缺位，后续扩展成本高。

### P1-2 参数优化引擎仍为轻量规则，不是网格/贝叶斯优化

现状证据：

- 已完成“研究结果读模型与参数空间校验”，但优化结果仍是规则驱动建议，未引入真实搜索算法。

对照源愿景：

- 需求文档明确“参数优化系统（网格搜索 + 贝叶斯优化）”：
  - `docs/需求分析最终版本.md`

风险：

1. 研究深度不足，难支撑高级用户策略优化；
2. 研究结果可解释性与可复算性边界仍弱。

### P2-1 策略组合（Portfolio）后端能力缺失

现状证据：

- 当前 `strategy-management` 尚无组合聚合、权重约束、再平衡接口与读模型；
- 源愿景明确包含“策略组合构建”。

风险：

1. 用户旅程止于“单策略研究”，无法进入组合构建与长期验证阶段；
2. 组合层风险暴露与绩效评估缺少统一后端模型。

## 3. 设计审查建议

1. **先把任务编排做实**：将领域任务从“同步假异步”迁移到“真实 dispatch + 可恢复执行”；
2. **再补流式能力**：以 market-data 为唯一市场流入口，避免监控/策略各自拉流；
3. **研究引擎与组合能力分拆演进**：先补优化算法，再扩到组合聚合，避免一次性过大改造；
4. **保持 Library-First**：优化/组合都先沉到独立库模块，再挂 API/CLI。

## 4. Wave7 OpenSpec 拆分（依赖 + 并行）

### 4.1 串行基座（先做）

1. `update-job-runtime-dispatch-integration`
   - 目标：业务任务统一走 `dispatch_job`，支持执行器模式切换与系统调度模板。
   - spec：`job-orchestration`

### 4.2 可并行包 A（基座后）

2. `add-market-data-stream-gateway`
   - 目标：新增市场数据流网关（WS/SSE 协议 + 鉴权 + 订阅模型）。
   - spec：`market-data`

3. `update-strategy-optimization-engine-grid-bayes`
   - 目标：把研究优化从规则建议升级为网格/贝叶斯优化任务。
   - spec：`strategy-management`

### 4.3 可并行包 B（A 后）

4. `add-strategy-portfolio-management`
   - 目标：新增策略组合聚合、权重约束、组合评估与再平衡任务。
   - spec：`strategy-management`（必要时新增 `strategy-portfolio` capability）

## 5. 依赖图

```text
update-job-runtime-dispatch-integration
    ├── add-market-data-stream-gateway
    └── update-strategy-optimization-engine-grid-bayes
            └── add-strategy-portfolio-management
```

## 6. 结论

Wave7 不再是“补齐 API 路径”，而是把后端从“可演示”推进到“可持续运行 + 可扩展研究”的阶段。

建议先评审并批准上述 4 个 OpenSpec，再按依赖顺序进入实现。
