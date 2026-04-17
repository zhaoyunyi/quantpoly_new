# 全栈 Coolify 部署手册（frontend + backend + postgres）

> 目标：在 Coolify 上以单个 Docker Compose 资源部署新前端与新后端，并覆盖线上流量。
>
> `2026-04-18` 已重新验证前端 npm 构建基线：`npm ci && npm run build` 可通过。收敛记录见：`docs/migration/2026-04-18-doc-code-consistency-audit.md`。

## 1. 对应部署资产

- Compose（生产推荐）：`docker-compose.coolify.yml`
- Compose（模板/参考）：`deploy/coolify/docker-compose.fullstack.yml`
- 前端镜像：`docker/frontend.prod.Dockerfile`
- 后端镜像：`docker/backend.prod.Dockerfile`
- 环境变量模板：`deploy/coolify/.env.fullstack.example`

## 2. 部署前准备

1. 在 Coolify 创建目标 Project/Environment（建议先 `staging` 后 `production`）。
2. 准备两个域名：
   - 前端：例如 `app.example.com`
   - 后端：例如 `api.example.com`
3. 准备 PostgreSQL 强密码（`POSTGRES_PASSWORD`）。
4. 如需实时行情，准备 Alpaca 凭据（可选）。

## 3. Coolify 资源创建

1. `Add Resource` → `Docker Compose`。
2. 选择仓库与分支。
3. `Compose Path` 填：`docker-compose.coolify.yml`。
4. 在 `Environment Variables` 中粘贴并修改 `deploy/coolify/.env.fullstack.example` 的变量。

关键变量最少需要：

- `POSTGRES_PASSWORD`
- `VITE_BACKEND_ORIGIN`
- `BACKEND_CORS_ALLOWED_ORIGINS`

推荐值示例：

- `VITE_BACKEND_ORIGIN=https://api.example.com`
- `BACKEND_CORS_ALLOWED_ORIGINS=https://app.example.com`
- `USER_AUTH_COOKIE_SECURE=true`
- `USER_AUTH_COOKIE_SAMESITE=lax`

## 4. 域名与端口绑定

- `frontend` 服务端口：`3000`，绑定 `app.example.com`
- `backend` 服务端口：`8000`，绑定 `api.example.com`
- `postgres` 不暴露公网

Coolify 控制台建议按下列位置配置：

- Resource 级：填写 `Environment Variables`（来自 `.env.fullstack.example`）
- Service `frontend`：`Domains` 添加 `app.example.com`，`Port` 选择 `3000`
- Service `backend`：`Domains` 添加 `api.example.com`，`Port` 选择 `8000`
- Service `postgres`：不添加域名，不开放公网端口

## 5. 首次部署与验证

1. 先在仓库内验证前端构建基线：

```bash
cd apps/frontend_web && npm run build
```

2. 如需验证锁文件可复现性，可在干净目录执行：

```bash
cd apps/frontend_web && npm ci && npm run build
```

3. 确认前端构建通过后，再点击 `Deploy`。
4. 等待三个服务都变为 `Healthy`。
5. 验证：

```bash
curl -f https://api.example.com/health
curl -I https://app.example.com/
```

6. 登录一次，确认响应头 `Set-Cookie` 带 `Secure`（生产环境必须）。

## 5.1 本地浏览器级部署验证

如需在本机模拟一套“接近 Coolify 生产编排”的全栈栈，并通过宿主机端口做浏览器验证，可使用：

- 基础编排：`docker-compose.coolify.yml`
- 本地 override：`docker-compose.coolify.local.yml`
- 一键脚本：`scripts/verify_coolify_local_stack.py`

最省事的入口：

```bash
./.venv/bin/python scripts/verify_coolify_local_stack.py
```

辅助开关：

- 只看执行计划：`./.venv/bin/python scripts/verify_coolify_local_stack.py --print-only`
- 验证完成后保留栈：`./.venv/bin/python scripts/verify_coolify_local_stack.py --keep-stack`

建议命令：

```bash
export POSTGRES_PASSWORD=quantpoly_local_pw
export VITE_BACKEND_ORIGIN=http://localhost:18000
export BACKEND_CORS_ALLOWED_ORIGINS=http://localhost:13000
export USER_AUTH_COOKIE_SECURE=false
export USER_AUTH_COOKIE_SAMESITE=lax

docker compose \
  -p quantpoly_local_browser \
  -f docker-compose.coolify.yml \
  -f docker-compose.coolify.local.yml \
  up -d --build
```

本地端口约定：

- frontend: `http://localhost:13000`
- backend: `http://localhost:18000`
- postgres: `localhost:15432`

验证要点：

- 三个服务都达到 `healthy`
- `curl http://localhost:18000/health`
- 浏览器访问 `http://localhost:13000/`
- 浏览器登录后跳转到 `/dashboard`
- 浏览器中存在后端 `session_token` cookie
- 如需跑完整浏览器回归：

```bash
cd apps/frontend_web && PLAYWRIGHT_BACKEND_PORT=18000 npx playwright test --config playwright.compose.config.ts
```

重要：

- 本地浏览器联调必须统一使用 `localhost`，不要混用 `127.0.0.1`
- 否则会出现 CORS origin 与 Cookie host 不一致，导致登录后无法建立会话

清理命令：

```bash
docker compose \
  -p quantpoly_local_browser \
  -f docker-compose.coolify.yml \
  -f docker-compose.coolify.local.yml \
  down -v
```

如需在干净 CI 环境重复执行同一条链路，仓库已提供工作流：

- `.github/workflows/verify-coolify-local-stack.yml`

## 6. 覆盖线上建议（低风险）

1. 先在 `staging` 验证回归。
2. `production` 部署完成后先不切流量。
3. 通过 DNS 或网关将流量逐步切到新服务。
4. 观察 30~120 分钟：
   - `/health` 可用
   - `/internal/metrics` 错误率稳定
   - 登录、鉴权、核心页面正常

## 7. 回滚策略

1. 保留旧版服务与旧域名解析。
2. 若异常，优先回滚流量（DNS/网关切回旧服务）。
3. 新版服务保持运行用于排查，不要先删库。

## 8. 已知约束

- 前端构建依赖 `VITE_BACKEND_ORIGIN` 的构建期注入；修改后端域名需重新部署前端。
- 当前方案默认后端任务执行模式为 `inprocess`，未启用独立 worker/redis。

## 9. 可选：Coolify API 自动化部署

如果需要我直接通过 API 代你执行部署，需要提供以下信息与权限：

- Coolify Base URL（例如 `https://coolify.example.com`）
- API Token（建议仅用于该 Project/Environment，避免全局管理员 Token）
- 目标 Project 名称或 ID
- 目标 Environment 名称或 ID（如 `staging`、`production`）
- 目标 Docker Compose Resource 名称或 ID

建议最小权限：

- 可读取并更新 Resource 的环境变量
- 可触发 Resource 重新部署
- 可读取部署状态与日志

不建议授予的权限：

- 全局删除资源权限
- 跨项目管理权限（除非你明确需要）
