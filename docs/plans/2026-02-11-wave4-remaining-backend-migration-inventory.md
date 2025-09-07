# 2026-02-11 Wave4 剩余后端功能迁移盘点与拆分

## 1. 盘点范围与方法

- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 对比维度：
  - 产品愿景与需求（`docs/需求分析最终版本.md`、`docs/项目总体架构设计.md`）
  - 路由能力面（source `app/api/routes/*.py` vs current `libs/*/*/api.py` + `user_auth` + `monitoring_realtime`）
  - 限界上下文能力完备性（user/strategy/backtest/trading/risk/signal/monitoring）

## 2. 产品愿景对齐结论

源项目愿景聚焦「个人量化研究与验证闭环」：

1. 策略模板化创建与执行；
2. 回测可解释结果与多维分析；
3. 模拟交易账本闭环（订单/成交/持仓/资金）；
4. 风险监控与告警闭环；
5. 用户分层与治理能力（Level 1/2、管理员动作）。

当前项目已经完成核心后端聚合与大部分域能力迁移（并已归档多个 parity change）。
剩余缺口已从“主干缺失”收敛为“边缘能力缺失与查询面不完整”。

## 3. 源/目标差异判定（能力视角）

## 3.1 已等价或可接受 break（无需继续迁移）

- `strategy-execution/*` 独立命名空间：已被 `signal-execution + strategy-management` 融合覆盖。
- `market/stocks|data` 老接口路径：已由 `market/catalog|history|quote|latest` 替代。
- `monitoring/summary` 路径：现有 `monitor/summary + ws/monitor` 能力更完整。
- `login/*` 老路径：当前 `user-auth` 已有注册/登录/会话/重置密码闭环。

## 3.2 仍建议补齐的剩余后端能力（真实缺口）

1. **回测管理读模型增强**
   - 缺口：回测名称重命名、同策略相关回测聚合查询。
   - 价值：提升回测分析可用性与可管理性。

2. **交易订单生命周期补齐**
   - 缺口：订单更新/删除（撤销语义收口）、按标的查询单仓位、账户级待处理成交列表。
   - 价值：交易账本从“可下单”升级为“可维护”。

3. **风险/信号查询面补齐**
   - 缺口：风险规则统计、近期告警快捷视图、手动信号过期、账户维度信号统计。
   - 价值：监控大盘与运营排障效率提升。

4. **管理员用户开通能力补齐**
   - 缺口：管理员创建用户（非自注册路径）与治理审计联动。
   - 价值：B2B/运营场景下用户开通、迁移与应急处理能力。

## 4. 架构合理性审查与调整建议

## 4.1 当前合理点

- DDD 上下文边界已稳定：`user-auth / strategy / backtest / trading / risk / signal`。
- 任务化编排能力充分（`job-orchestration` 覆盖度高）。
- 用户系统已完成后端聚合，前端不再承担会话/权限真相源。

## 4.2 建议调整点（面向剩余迁移）

1. **回测读模型增强**：在 `backtest-runner` 内补 `metadata + related` 查询，避免跨域拼接。
2. **交易生命周期一致性**：订单修改/撤销必须限定 `pending/open` 状态并写审计事件。
3. **查询快捷视图策略**：对 `recent/unresolved/stats` 这种运营视图建立稳定读模型，避免前端拼装。
4. **管理员动作统一治理**：管理员建用户动作需接入 `admin-governance` 审计，保持可追踪。

## 5. Wave4 OpenSpec 拆分（按依赖/并行性）

## 5.1 并行包 A（可并行）

1. `update-backtest-management-readmodel-parity`
2. `update-trading-order-amendment-parity`

## 5.2 并行包 B（可并行）

3. `update-risk-signal-query-parity`
4. `update-user-admin-provisioning-parity`

## 5.3 依赖说明

- 四项之间无强硬串行依赖，可并行推进。
- 但 `update-user-admin-provisioning-parity` 落地时必须复用 `admin-governance`（不允许旁路鉴权）。

## 6. 执行建议

- 先实现 A 组（业务主链收益更直接）；
- 再实现 B 组（运营治理收益）；
- 每项按 Library-First + CLI Mandate + TDD 执行，并在完成后独立归档。
