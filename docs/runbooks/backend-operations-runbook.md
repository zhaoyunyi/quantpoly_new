# 后端运行手册（单一入口）

> 本文档用于发布/切换/联调时的统一操作基线，内容仅保留与当前代码实现一致的规则。

文档导航入口：`docs/README.md`。

## 1. 当前契约基线

### 1.1 响应信封

- 成功响应：`success_response` / `paged_response`
- 错误响应：`error_response`
- 调用方应优先解析：`success`、`error.code`、`error.message`

### 1.2 用户资源路由

- 当前用户主路径：`/users/me`
- 兼容移除提示：`GET /auth/me` 返回 `410` 与 `error.code=ROUTE_REMOVED`

## 2. 切换前冒烟

执行：

```bash
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

脚本检查项（与当前脚本一致）：

- `health`
- `auth_register`
- `auth_verify_email`
- `auth_login`
- `strategy_list`
- `monitor_summary`
- `ws_monitor`

放行条件：脚本输出 `success=true`。

## 3. 切换后观测

### 3.1 指标端点

- 指标读取：`GET /internal/metrics`
- 关键字段：
  - `httpRequestsTotal`
  - `httpErrorsTotal`
  - `httpErrorRate`
  - `timestamp`

### 3.2 观测建议阈值

> 下列阈值为运行建议，用于告警与回滚决策，不代表接口硬编码限制。

- 建议错误率：`httpErrorRate <= 0.05`
- 监控链路：`/monitor/summary` 与 `/ws/monitor` 同时可用
- 鉴权失败结构：`{"success":false,"error":{"code","message"}}`

## 4. 回滚触发建议

满足任一条件建议回滚：

- 关键接口持续 5 分钟不可用
- `httpErrorRate > 0.10` 且持续 3 分钟
- 出现跨用户数据泄露告警

回滚后请保留以下证据用于复盘：

- 冒烟脚本输出 JSON
- `/internal/metrics` 快照

## 5. 门禁命令

### 5.1 能力门禁

```bash
cat docs/gates/examples/capability_gate_input.json | python3 -m platform_core.cli capability-gate
```

### 5.2 存储契约防回流门禁

```bash
python3 -m platform_core.cli storage-contract-gate
```
