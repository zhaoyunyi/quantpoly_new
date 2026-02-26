# 后端门禁手册（单一入口）

> 本文档定义当前仓库可执行的门禁规则，且仅保留与代码实现一致的内容。

## 1. 能力门禁（`capability-gate`）

### 1.1 命令

```bash
cat docs/gates/examples/capability_gate_input.json | python3 -m platform_core.cli capability-gate
```

### 1.2 输入结构

能力门禁输入 JSON 字段：

- `wave`：波次标识（字符串）
- `capabilities`：能力列表（数组）
  - `id`：能力 ID
  - `passed`：是否通过
  - `critical`：是否关键能力
  - 可选辅助字段：`context`、`journey`
- `postCutoverMetrics`：切换后指标（对象）
  - `errorRate`
  - `p95LatencyMs`
  - `queueBacklog`
  - `dataLeakage`
- `thresholds`：阈值（可选，对象）
  - `maxErrorRate`（默认 `0.05`）
  - `maxP95LatencyMs`（默认 `800`）
  - `maxQueueBacklog`（默认 `200`）

样例输入：`docs/gates/examples/capability_gate_input.json`

### 1.3 判定规则（与实现一致）

规则来源：`libs/platform_core/platform_core/capability_gate.py`

#### 阻断条件（`allowed=false`）

满足任一条件即阻断：

- 任一能力 `passed=false`
- `errorRate > maxErrorRate`
- `p95LatencyMs > maxP95LatencyMs`
- `queueBacklog > maxQueueBacklog`
- `dataLeakage=true`

#### 回滚建议（`rollbackRequired=true`）

在 `allowed=false` 且满足任一条件时触发：

- 存在关键能力失败（`critical=true` 且 `passed=false`）
- `dataLeakage=true`
- `errorRate > maxErrorRate`

### 1.4 输出关键字段

- `allowed`
- `rollbackRequired`
- `blockers`
- `summary.{total,passed,failed,criticalFailed}`
- `metrics`
- `thresholds`

## 2. 存储契约防回流门禁（`storage-contract-gate`）

### 2.1 命令

```bash
python3 -m platform_core.cli storage-contract-gate
```

### 2.2 判定目标

规则来源：`libs/platform_core/platform_core/storage_contract_gate.py`

- 默认扫描核心上下文库 `__all__` 导出
- 拦截包含 `sqlite` / `SQLite` 的导出标识
- 输出模块级违规明细（`violations`）

### 2.3 输出关键字段

- `allowed`
- `source`
- `forbiddenTokens`
- `summary.{checkedModules,checkedExports,violations}`
- `modules`
- `violations`

## 3. 运营建议阈值（用于告警与决策）

> 以下阈值是运行建议，可用于发布门禁与告警阈值配置：

- `errorRate <= 0.05`
- 监控链路 `/monitor/summary` 与 `/ws/monitor` 同时可用
- 鉴权失败响应保持错误信封结构：`{"success":false,"error":{"code","message"}}`
