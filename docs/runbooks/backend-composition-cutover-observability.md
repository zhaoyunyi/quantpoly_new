# backend composition root 切换观测与冒烟方案

## 1. 切换前冒烟脚本

执行：

```bash
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

脚本输出 JSON，至少包含以下检查项：

- `health`
- `auth_register`
- `auth_verify_email`
- `auth_login`
- `strategy_list`
- `monitor_summary`
- `ws_monitor`

`success=true` 才允许执行波次切换。

## 2. 切换后观测指标

统一从组合入口 `/internal/metrics` 读取：

- `httpRequestsTotal`
- `httpErrorsTotal`
- `httpErrorRate`
- `timestamp`

## 3. 阈值建议（观察窗口）

- 错误率阈值：`httpErrorRate <= 0.05`
- 任意上下文鉴权失败结构必须保持统一信封：`{"success":false,"error":{"code","message"}}`
- 实时监控链路可用性：`/monitor/summary` 与 `/ws/monitor` 同时可用

## 4. 回滚触发建议

满足任一条件触发回滚：

- 关键接口持续 5 分钟不可用（401/403 语义漂移或 5xx 激增）
- `httpErrorRate > 0.10` 且持续 3 分钟
- 出现跨用户数据泄露告警

回滚后需保留 `smoke` 输出与 `/internal/metrics` 快照用于复盘。
