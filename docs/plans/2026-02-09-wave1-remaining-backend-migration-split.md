# 2026-02-09 Wave1 剩余后端功能迁移拆分（OpenSpec）

## 1. 盘点结论（基于源仓库静态扫描）

对源项目 `quantpoly-backend/backend/app/api/routes` 与当前仓库后端能力对照后，剩余缺口集中在三类：

1. **用户生命周期闭环**：缺少用户自助注销（账号删除）与管理员用户销毁闭环。
2. **策略执行引擎控制面**：缺少参数校验、信号生成/处理、执行详情与运行中视图等执行控制面。
3. **交易高级分析与运维面**：缺少账户级风险指标、权益曲线、仓位分析、交易运维接口（如待处理交易与价格刷新）。

> 说明：本轮采用“允许 break，但能力不缺失”的策略，不追求路径级兼容，仅追求能力等价与治理一致性。

## 2. 新增 OpenSpec 变更（Wave1）

- `update-user-lifecycle-deletion-parity`
- `update-strategy-execution-control-parity`
- `update-trading-analytics-ops-parity`

## 3. 依赖关系与并行性

### 3.1 可并行

- `update-user-lifecycle-deletion-parity`
- `update-strategy-execution-control-parity`

二者主要依赖已完成的统一鉴权与组合入口，不相互阻塞。

### 3.2 建议串行（后置）

- `update-trading-analytics-ops-parity`

依赖交易账本与风险上下文的稳定读模型，建议在上两项接口治理收口后推进，以减少口径返工。

## 4. 执行顺序建议

1. 先落地 `update-user-lifecycle-deletion-parity`（治理风险最高）。
2. 并行推进 `update-strategy-execution-control-parity`（补齐策略执行闭环）。
3. 最后执行 `update-trading-analytics-ops-parity`（高级分析与运维面）。

## 5. 验收口径

- 所有新增能力必须提供 **Library + CLI + API** 三层入口。
- 所有新增写操作必须走 **TDD（Red→Green→Refactor）**。
- 所有新增接口必须满足：
  - 用户所有权校验；
  - 统一错误 envelope 与错误码；
  - 审计日志与敏感字段脱敏。
