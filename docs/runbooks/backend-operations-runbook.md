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

### 1.3 前端直连后端（CORS + Cookie 会话）

当前前端采用浏览器端 **HTTP 直连后端** 的方式联调，后端需开启 CORS 以允许跨 Origin 携带 `session_token` cookie（credentials）。

推荐开发期统一使用 `localhost`（避免 `localhost` 与 `127.0.0.1` 混用导致 cookie/WS 鉴权异常）：

- 前端：`http://localhost:3300`
- 后端：`http://localhost:8000`

后端 CORS 配置（默认关闭）：

- `BACKEND_CORS_ALLOWED_ORIGINS`：允许的前端 origin 白名单（逗号分隔），示例：`http://localhost:3300`
- `BACKEND_CORS_ALLOW_CREDENTIALS`：是否允许 credentials（默认 `true`）
- `BACKEND_CORS_ALLOW_METHODS`：允许方法（逗号分隔，默认 `GET,POST,PUT,PATCH,DELETE,OPTIONS`）
- `BACKEND_CORS_ALLOW_HEADERS`：允许头（逗号分隔，默认 `*`）

### 1.4 本地联调一键脚本（推荐）

脚本：`scripts/local_dev_stack.py`

常用命令：

```bash
# 预览将执行的命令、环境变量、日志路径（不实际启动）
./.venv/bin/python scripts/local_dev_stack.py up --print-only

# 一键启动前后端联调（默认：frontend=3300、backend=8000、backend=memory）
./.venv/bin/python scripts/local_dev_stack.py up

# 查看当前运行状态（PID / origin / 日志）
./.venv/bin/python scripts/local_dev_stack.py status

# 停止一键脚本拉起的前后端进程
./.venv/bin/python scripts/local_dev_stack.py down
```

补充：

- `up` 默认会执行启动后冒烟（`scripts/smoke_backend_composition.py`）；如需跳过可加 `--skip-smoke`
- 默认状态文件与日志目录：`.tmux-logs/local_dev_stack/`

### 1.5 Docker 本地后端热更新联调

脚本：`scripts/backend_docker_dev.sh`

默认行为：

- 通过 `docker-compose.backend-dev.yml` 构建并启动 `postgres + backend_dev`
- 后端容器端口映射为 `localhost:8000`
- CORS 默认放行 `http://localhost:3300`
- 后端以 `uvicorn --reload` 运行，代码目录挂载 `./:/workspace`，本地改代码会自动热更新

常用命令：

```bash
# 预览将执行的命令与环境变量（不实际启动）
bash scripts/backend_docker_dev.sh up --print-only

# 一键构建并启动（frontend 默认通过 http://localhost:3300 访问 http://localhost:8000）
bash scripts/backend_docker_dev.sh up

# 查看容器状态
bash scripts/backend_docker_dev.sh status

# 查看后端日志
bash scripts/backend_docker_dev.sh logs

# 停止并移除本脚本创建的容器/网络
bash scripts/backend_docker_dev.sh down
```

可选环境变量（示例）：

```bash
# 避免本机 8000 端口冲突
BACKEND_PORT=18000 bash scripts/backend_docker_dev.sh up

# 切换后端存储为内存（不依赖 Postgres）
BACKEND_STORAGE_BACKEND=memory bash scripts/backend_docker_dev.sh up
```

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
