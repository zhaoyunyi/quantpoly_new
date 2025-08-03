# OpenSpec 归档执行计划（2026-02-08）

## 1. 当前状态盘点

### 1.1 已完成但未归档的 Change

- `update-user-system-backend-consolidation`
- `add-strategy-backtest-migration`
- `add-trading-account-context-migration`
- `add-market-data-context-migration`
- `add-risk-signal-context-migration`
- `update-monitoring-realtime-full-streaming`
- `add-data-topology-boundary-migration`
- `add-job-orchestration-context-migration`
- `add-admin-governance-context-migration`

### 1.2 当前 Spec 基线

当前 `openspec list --specs` 已存在：

- `backend-user-ownership`
- `monitoring-realtime`
- `platform-core`
- `user-auth`
- `user-preferences`

归档完成后预期新增（或更新）：

- 新增：`strategy-management`、`backtest-runner`、`trading-account`、`market-data`、`risk-control`、`signal-execution`、`data-topology-boundary`、`job-orchestration`、`admin-governance`
- 更新：`user-auth`、`user-preferences`、`monitoring-realtime`

---

## 2. 归档原则

1. **按依赖顺序分批归档**，避免大量 delta 一次性合并导致冲突难排查。
2. 每归档 1 个 change 后立即执行：
   - `openspec validate --strict`
   - `pytest -q`（确保规格合入后行为仍一致）
3. 每个批次完成后单独提交（使用 `git cnd`）。
4. 归档使用：`openspec archive <change-id> --yes`（**不加 `--skip-specs`**，需要更新 specs 真相）。

---

## 3. 分批归档顺序

## Batch A（用户基座）

1. `update-user-system-backend-consolidation`

原因：会更新 `user-auth`/`user-preferences` 规格，属于后续能力共用基础。

## Batch B（核心业务能力）

2. `add-strategy-backtest-migration`
3. `add-trading-account-context-migration`
4. `add-market-data-context-migration`

原因：这三者是风控、信号、监控的上游能力。

## Batch C（风控执行与实时）

5. `add-risk-signal-context-migration`
6. `update-monitoring-realtime-full-streaming`

原因：监控依赖信号与风险数据结构。

## Batch D（基础治理层）

7. `add-data-topology-boundary-migration`
8. `add-job-orchestration-context-migration`
9. `add-admin-governance-context-migration`

原因：属于平台治理与运行时能力，适合作为后置归档收口。

---

## 4. 命令执行模板

### 4.1 单个 Change 归档模板

```bash
openspec archive <change-id> --yes
openspec validate --strict
pytest -q
```

### 4.2 单个 Batch 完成后提交模板

```bash
git add openspec/specs openspec/changes/archive
git cnd -m "chore(openspec): archive <batch-name>"
```

---

## 5. 建议的实际执行清单（可直接复制）

```bash
# Batch A
openspec archive update-user-system-backend-consolidation --yes
openspec validate --strict
pytest -q
git add openspec/specs openspec/changes/archive
git cnd -m "chore(openspec): archive batch-a user-foundation"

# Batch B
openspec archive add-strategy-backtest-migration --yes
openspec archive add-trading-account-context-migration --yes
openspec archive add-market-data-context-migration --yes
openspec validate --strict
pytest -q
git add openspec/specs openspec/changes/archive
git cnd -m "chore(openspec): archive batch-b core-domains"

# Batch C
openspec archive add-risk-signal-context-migration --yes
openspec archive update-monitoring-realtime-full-streaming --yes
openspec validate --strict
pytest -q
git add openspec/specs openspec/changes/archive
git cnd -m "chore(openspec): archive batch-c risk-signal-monitoring"

# Batch D
openspec archive add-data-topology-boundary-migration --yes
openspec archive add-job-orchestration-context-migration --yes
openspec archive add-admin-governance-context-migration --yes
openspec validate --strict
pytest -q
git add openspec/specs openspec/changes/archive
git cnd -m "chore(openspec): archive batch-d platform-governance"

# 最终校验
openspec validate --strict
pytest -q
```

---

## 6. 风险与回滚预案

1. 若某个 change 归档后出现 spec 冲突：
   - 先 `git status` 定位冲突文件
   - 仅回退该 change 归档相关改动（`git restore` 指定文件）
   - 单独执行该 change 的 `openspec show <change-id> --json --deltas-only` 重新检查 delta

2. 若归档后测试失败：
   - 优先定位是否为“规格真相合并后暴露的既有代码缺口”
   - 在新 change 中修复，不在归档提交里混入业务修复

3. 若需中断批次：
   - 批次内不提交，直接回滚工作区，保持“每批次一个干净提交”

---

## 7. 建议执行方式

- 推荐按 **Batch A → B → C → D** 顺序推进。
- 每批次完成后立即创建可审阅提交，便于回滚与审计。
- 若你同意，我可以下一步直接按本计划从 **Batch A** 开始代执行归档与提交。

