# 2026-02-11 Wave5 剩余后端功能迁移盘点与拆分

## 1. 盘点目标与输入

- 目标：在已完成 Wave1~Wave4 大量 parity 迁移后，识别**源项目仍有而当前后端尚未完整承接**的能力，并按依赖与可并行性拆分下一批 OpenSpec。
- 源项目：`/Users/zhaoyunyi/developer/claude-code/quantpoly/quantpoly-backend/backend`
- 当前项目：`/Users/zhaoyunyi/developer/quantpoly`
- 关键输入：
  - 产品与需求文档：`docs/需求分析最终版本.md`、`docs/specs/mvp-spec.md`、`docs/项目总体架构设计.md`（源项目）
  - 路由能力面对比：source `backend/app/api/routes/*.py` vs current `libs/*/*/api.py` + `apps/backend_app/router_registry.py`
  - 当前规范约束：`spec/ProgramSpec.md`、`spec/DDDSpec.md`、`spec/BDD_TestSpec.md`

## 2. 产品愿景与需求对齐结论

源项目愿景仍是「个人量化研究与验证闭环」，核心不是旧接口路径一致，而是业务能力不缺失：

1. 策略模板 → 参数校验 → 信号生成/执行闭环；
2. 模拟交易从下单到成交再到账户统计闭环；
3. 回测/风控/监控支持研究与运营场景，而不止 CRUD；
4. 用户与管理员治理动作统一后端托管。

当前项目已经完成主干能力迁移，且用户系统已后端聚合（符合 hard-cutover）。
但在“**执行入口完整性**”与“**运行时持久化/数据真实性**”上仍有缺口，需要进入 Wave5。

## 3. 剩余缺口盘点（功能 + 架构）

## 3.1 功能层剩余缺口（P0，影响业务闭环）

1. **交易一键指令入口缺口（buy/sell command）**
   - 现状：当前以 `orders` 生命周期为主（下单/改单/撤单/成交），能力完整但偏“交易后台视角”。
   - 缺口：缺少面向产品层的“一键买入/卖出”指令入口（源项目有 `buy/sell` 业务语义）。
   - 风险：前端或自动化策略侧需要自行拼装多步流程，增加耦合与误用概率。

2. **策略执行查询语义缺口（template-by-type / strategy-level stats）**
   - 现状：已有 `signals/*` 与 `signals/executions/*` 体系。
   - 缺口：缺少“按策略类型模板查询”与“按策略维度统计/趋势”的稳定查询语义收口（当前能力分散在 strategy-management 与 signal-execution 两侧）。
   - 风险：前端/运营端需要跨上下文拼装统计口径。

## 3.2 架构层剩余缺口（P0，影响稳定性）

3. **组合入口仍混用 InMemory 仓储（risk/signal/preferences）**
   - 现状：`apps/backend_app/router_registry.py` 在 `sqlite` 模式下仍实例化 `InMemoryRiskRepository`、`InMemorySignalRepository`、`InMemoryPreferencesStore`。
   - 缺口：服务重启后状态丢失，无法满足运营审计与持续监控。
   - 风险：风险告警、信号执行历史、偏好配置在长周期场景不可靠。

4. **市场数据运行时仍默认 InMemory Provider**
   - 现状：组合入口默认 `_InMemoryMarketProvider`，报价可用但为占位语义。
   - 缺口：未将 `market_data/alpaca_provider.py` 等真实 provider 能力接入运行时配置。
   - 风险：回测/交易/风控链路基于占位行情，产品价值与真实度不足。

## 3.3 可接受 break（不作为 Wave5 必做）

以下属于“兼容路径差异”而非“功能缺失”，可继续保持 break-update：

- `strategy-execution/*` 旧命名空间已并入 `signal-execution + strategy-management`；
- `risk-control/*` 旧前缀已收口到 `risk/*`；
- `/users/*` 管理路由已收口为 `/admin/users/*`；
- `/utils/test-email`、`/password-recovery-html-content` 等调试/运维辅助端点可不迁移。

## 4. 架构合理性审查（针对当前后端）

## 4.1 当前合理点

- 限界上下文边界已较清晰：`user-auth / strategy-management / backtest-runner / trading-account / risk-control / signal-execution / market-data`；
- 组合入口统一治理（鉴权、脱敏日志、错误包络）方向正确；
- 任务编排（job-orchestration）已形成可复用基座。

## 4.2 需要调整点（建议在 Wave5 落地）

1. **持久化策略统一化**
   - 为 risk/signal/preferences 增加 sqlite 适配仓储，并在组合入口依据 `storage_backend` 自动注入。
2. **运行时 provider 插拔化**
   - 将 market provider 从硬编码 InMemory 改为配置驱动（内存/Alpaca/Mock）。
3. **跨上下文查询口径收敛**
   - 将策略执行统计口径收敛为单一后端读模型，避免前端拼装。
4. **交易命令入口与账本模型解耦**
   - 在不破坏订单聚合的前提下提供 buy/sell command façade，保持 domain intent 清晰。

## 5. Wave5 OpenSpec 拆分（按依赖/可并行）

## 5.1 串行基座（先做）

1. `update-runtime-persistence-provider-baseline`
   - 目标：组合入口支持可配置仓储与 provider 注入；
   - 覆盖：risk/signal/preferences 的持久化接入点、market provider runtime 选择。

> 说明：该项不要求一次性完成全部域实现，但必须先建立统一注入协议和配置约束。

## 5.2 并行包 A（功能闭环，可并行）

2. `update-trading-command-entry-parity`
   - 目标：补齐 buy/sell 业务命令入口（可作为 order 流程 façade），并提供明确错误语义与审计事件。

3. `update-strategy-execution-query-readmodel`
   - 目标：补齐策略执行模板按类型查询、按策略统计/趋势查询收口，统一与 signal-execution 读模型口径。

## 5.3 并行包 B（状态可靠性，可并行）

4. `update-risk-signal-persistence-adapters`
   - 目标：为 risk-control/signal-execution 提供 sqlite 持久化仓储与迁移脚本。

5. `update-user-preferences-persistent-adapter`
   - 目标：将 `user-preferences` 从 InMemory 接入可持久化存储并纳入组合入口装配。

6. `update-market-data-provider-runtime-parity`
   - 目标：接入 Alpaca provider（或等价真实 provider）到 runtime 配置，保留 mock/inmemory 作为开发选项。

## 5.4 依赖关系

- `update-runtime-persistence-provider-baseline` 完成后，5.3 三项可并行推进；
- 5.2 与 5.3 可并行，但 `update-strategy-execution-query-readmodel` 需复用统一口径定义（避免后续返工）；
- 所有变更落地后再进行统一回归与归档。

## 6. 实施策略（符合 spec 规范）

1. **Library-First**：每项变更先补库能力，再暴露 API；
2. **CLI Mandate**：每个库新增能力必须同时提供 CLI 命令（stdin/args/file + JSON 输出）；
3. **Test-First**：先写失败测试（Red）再实现；
4. **DDD 约束**：跨上下文通过 ACL/OHS 协议，不允许跨域直连仓储；
5. **BDD 输出**：核心验收场景使用 Given/When/Then，并遵守 snake_case 输出。

## 7. 建议执行顺序

- 第 1 步：创建并评审 `update-runtime-persistence-provider-baseline`；
- 第 2 步：并行推进 A/B 两组；
- 第 3 步：跨上下文回归（交易+策略+信号+风控+监控）后统一归档。

---

该盘点采用“功能不缺失优先，兼容路径可 break”的迁移策略，下一步可直接基于上述 6 个 change-id 批量生成 OpenSpec proposal/tasks/spec delta。
