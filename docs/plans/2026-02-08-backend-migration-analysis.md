# QuantPoly 后端迁移审查与拆分方案（源项目 → 当前仓库）

## 1. 审查范围与结论

- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly`
  - 后端：`quantpoly-backend/backend`
  - 前端：`quantpoly-frontend`
- 目标项目：`/Users/zhaoyunyi/developer/quantpoly`
  - 当前能力：`platform_core`、`user_auth`、`user_preferences`、`monitoring_realtime`

### 总体结论

1. **源项目“用户系统”仍明显前端持有**：认证实例创建、D1 绑定、认证路由、token 获取与缓存、鉴权中间件均在前端代码内。
2. **源后端存在“JWT + better-auth 混合态”**：`login/access-token` 仍走 JWT，而大多数业务路由走 `better-auth` 会话校验，语义不统一。
3. **权限与所有权控制不稳定**：大量端点声明了 `Depends(get_current_user)`，但未使用 `current_user` 过滤资源。
4. **当前仓库已具备迁移落脚点**（`user_auth`/`user_preferences`/`platform_core`），但仍是最小实现，尚未覆盖源项目完整能力（邮箱验证、密码找回、持久化会话、复杂偏好契约等）。

---

## 2. 源项目关键实现问题（含可定位证据）

## 2.1 可确认 bug / 高风险缺陷

- **删除用户接口存在未定义符号，运行时会报错**
  - `.../quantpoly-backend/backend/app/api/routes/users.py:383`
  - `delete(Item)` 中 `Item` 未定义；`ruff --select F821` 已可复现。

- **多处接口“已认证但未做所有权约束”**（越权风险）
  - 示例：`.../app/api/routes/signals.py:450`、`:482`、`:501`、`:548`
  - 示例：`.../app/api/routes/risk_control.py:394`、`:420`、`:446`、`:466`、`:482`
  - 示例：`.../app/api/routes/strategy_execution.py:507`、`:593`

- **敏感信息日志泄漏风险**
  - WebSocket 认证失败日志直接打印 cookies/header：
  - `.../app/auth/dependencies.py:243-247`
  - 前端认证路由打印请求体片段：
  - `.../quantpoly-frontend/app/api/auth/[...all]/route.ts:115-117`

## 2.2 设计一致性问题

- **鉴权体系双轨**（JWT 与 better-auth 并存）
  - `.../app/api/deps.py`（JWT）
  - `.../app/auth/dependencies.py`（better-auth 会话）

- **前端承担后端职责**（违反“用户系统聚合到后端”）
  - 认证核心在前端：`.../quantpoly-frontend/lib/auth.ts`
  - 前端认证 API 网关：`.../app/api/auth/[...all]/route.ts`
  - 前端 D1 绑定与数据库选择：`.../lib/auth-database.ts`
  - 前端鉴权中间件：`.../middleware.ts`

- **响应契约不统一**
  - 部分接口返回标准 envelope，部分直接返回裸 dict/list。
  - `strategy_execution/signals/risk_control` 等模块存在不一致，增加前端适配复杂度。

- **偏好契约前后端分裂**
  - 前端 `UserPreferencesSchema`（字符串版本 `1.0.0` + 大量字段）与后端最小模型并不一致。

---

## 3. 功能依赖图（用于迁移排序）

## 3.1 强依赖（先做）

1. `user-auth`（统一鉴权、会话、权限入口）
2. `user-preferences`（用户体验与权限层）
3. `backend-user-ownership`（所有业务资源 user_id 约束）

## 3.2 中间层（可并行）

- `strategy-management`（策略）
- `backtest-runner`（回测）
- `trading-account`（账户/持仓/交易/资金流水）
- `market-data`（行情）

## 3.3 上层聚合（后做）

- `risk-control`（依赖 trading/account 数据）
- `signal-execution`（依赖 strategy + trading + risk）
- `monitoring-realtime`（依赖 signals + alerts + account 状态）

---

## 4. 串并行迁移建议

## 4.1 串行主链

`用户系统聚合` → `策略/回测` 与 `交易账户`（并行）→ `风险/信号执行` → `实时监控`

## 4.2 可平行迁移的工作包

- 包 A：`strategy-management` + `backtest-runner`
- 包 B：`trading-account`
- 包 C：`market-data`

> 其中 A/B/C 均依赖用户体系与所有权基座完成后再启动。

---

## 5. 拆分后的 OpenSpec 变更清单（本次已落地）

1. `update-user-system-backend-consolidation`
2. `add-strategy-backtest-migration`
3. `add-trading-account-context-migration`
4. `add-risk-signal-context-migration`
5. `add-market-data-context-migration`
6. `update-monitoring-realtime-full-streaming`

## 5.1 建议追加拆分（补齐当前覆盖缺口）

7. `add-job-orchestration-context-migration`
   - 来源：`backend/app/worker/celery_app.py` + `worker/tasks/*.py`
   - 价值：统一长任务编排、幂等、重试、调度、审计；避免业务路由阻塞化。

8. `add-admin-governance-context-migration`
   - 来源：signals/strategy_execution/risk_control 中的维护类与批量管理动作
   - 价值：统一管理员动作治理，收敛“认证通过但授权不足”的高风险入口。

9. `add-data-topology-boundary-migration`
   - 来源：`core/database_router.py` 的双库路由（D1/SQLite + PostgreSQL）
   - 价值：先固化数据边界与迁移规则，降低后续业务迁移反复改库的代价。

每个变更均已包含：
- `proposal.md`
- `tasks.md`
- 对应 capability 的 `spec delta`

---

## 6. 下一步执行建议

1. 先评审并批准 `update-user-system-backend-consolidation`。
2. 在批准后优先执行该变更（用户系统聚合是后续所有业务迁移前提）。
3. A/B/C 三个中间层变更在资源允许时并行推进。
4. 待 A/B 完成后再执行 `add-risk-signal-context-migration` 与 `update-monitoring-realtime-full-streaming`。

## 6.1 建议迁移波次（含新增拆分）

- **Wave 0（基座）**：`update-user-system-backend-consolidation` + `add-data-topology-boundary-migration`
- **Wave 1（核心能力）**：`add-strategy-backtest-migration` + `add-trading-account-context-migration` + `add-market-data-context-migration`
- **Wave 2（调度层）**：`add-job-orchestration-context-migration`
- **Wave 3（风控执行）**：`add-risk-signal-context-migration` + `add-admin-governance-context-migration`
- **Wave 4（实时运营）**：`update-monitoring-realtime-full-streaming`
