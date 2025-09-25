# strategy-management 策略研究优化深度迁移说明（break update）

## 背景

`/strategies/{id}/research/optimization-task` 已从“轻量建议任务”升级为“可配置优化研究任务”。

本次升级引入了以下后端能力：

- 结构化优化目标（`objective`）
- 结构化参数搜索空间（`parameterSpace`）
- 结构化约束（`constraints`）
- 可查询研究结果读模型（`/research/results`）

## break update 影响

这是一次 **break update**：

1. 优化任务结果结构从旧 `parameterRange + suggestions` 升级为 `optimizationResult`（v2）。
2. 参数空间进入严格校验，非法范围（如 `max < min`）会直接返回 `RESEARCH_INVALID_PARAMETER_SPACE`，并拒绝创建任务。
3. 新增研究结果查询接口，调用方应改为通过读模型获取历史研究结果，而非仅依赖任务提交即时返回。

## API 变更

### 1) 提交研究优化任务

`POST /strategies/{strategy_id}/research/optimization-task`

新增可选请求体字段：

- `objective`
  - `metric`：目标指标（默认 `averagePnl`）
  - `direction`：`maximize|minimize`（默认 `maximize`）
- `parameterSpace`
  - 每个参数要求 `min/max/step`
  - 当 `max < min` 或 `step <= 0` 时，返回 422
- `constraints`
  - 业务约束对象（可选）

错误码新增：

- `RESEARCH_INVALID_PARAMETER_SPACE`（422）

### 2) 查询研究结果

`GET /strategies/{strategy_id}/research/results`

查询参数：

- `status`：`succeeded|failed|cancelled`（可选）
- `limit`：返回条数（默认 20）

返回：

- `items[]`：每条包含 `taskId/taskType/status/optimizationResult/error/...`
- `total`：过滤后的总条数

权限：

- 非所有者返回 `STRATEGY_ACCESS_DENIED`（403）

## CLI 变更

### 1) 扩展命令

`research-optimization-task` 新增：

- `--objective-json`
- `--parameter-space-json`
- `--constraints-json`

参数空间非法时返回：`RESEARCH_INVALID_PARAMETER_SPACE`。

### 2) 新增命令

`research-results`

- `--user-id`
- `--strategy-id`
- `--status`
- `--limit`

用于读取研究结果历史读模型。

## 可观测信息

优化任务结果新增 `metadata`：

- `taskLatencyMs`：任务处理耗时（毫秒）
- `constraintsKeys`：约束键摘要
- `inputEcho`：目标与参数空间回显（脱敏结构）

## 迁移建议

1. 前端/调用方提交优化任务时，补齐 `objective/parameterSpace/constraints` 输入。
2. 对 `RESEARCH_INVALID_PARAMETER_SPACE` 做显式提示与纠正引导。
3. 将“研究结果展示”改为读取 `/research/results`，不要只读提交接口即时返回。
4. 对失败/取消结果分别做状态分组展示，避免与成功结果混淆。

## 回滚策略

- 若需临时回滚消费侧，可保留仅展示 `taskId/taskType/status` 的最小路径。
- 不建议回退后端校验逻辑；否则会重新引入无效参数进入任务系统的问题。
