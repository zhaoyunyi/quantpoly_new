# 全栈 Coolify 部署手册（frontend + backend + postgres）

> 目标：在 Coolify 上以单个 Docker Compose 资源部署新前端与新后端，并覆盖线上流量。
>
> `2026-04-18` 已重新验证前端 npm 构建基线：`npm ci && npm run build` 可通过。收敛记录见：`docs/migration/2026-04-18-doc-code-consistency-audit.md`。

## 0. 当前生产资源快照（2026-05-01）

- Coolify 控制台：`https://coolify.quantpoly.com/`
- Project：`QuantPoly_Backend`
- Environment：`production`
- Application：`quantpoly-fullstack-root`
- Application UUID：`wgsoo0gow8wkwow8kkg00kks`
- Source：`zhaoyunyi/quantpoly_new`
- Branch：`master`
- Compose Path：`/docker-compose.coolify.yml`
- 生产服务器 IP：`152.53.243.63`
- 当前已验证状态：
  - Coolify Application `running:healthy`
  - 后端 `https://api.quantpoly.com/health` 返回 200
  - 前端 `https://quantpoly.com/` 与 `https://www.quantpoly.com/` 经 Cloudflare 返回新 Vite/TanStack 前端 HTML
  - 旧 Worker `quantpoly-frontend` 的 `quantpoly.com/*`、`www.quantpoly.com/*` 路由已从 Cloudflare Dashboard 删除

当前仓库内只有本地 Coolify 栈验证工作流：

- `.github/workflows/verify-coolify-local-stack.yml`

截至本快照，仓库中没有“推送后由 GitHub Actions 触发生产 Coolify 部署”的 workflow。若 Coolify 控制台里开启了 GitHub webhook / auto deploy，那是 Coolify 侧配置；仓库内可审计、可重复执行的生产发布入口以 `scripts/deploy_coolify_production.py` 为准。

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

## 5.2 生产部署触发（当前推荐入口）

本地令牌文件放在：

- `deploy/secrets/ops_tokens.local.env`

该文件必须保持本地私有，不提交。最小内容示例：

```bash
COOLIFY_BASE_URL=https://coolify.quantpoly.com/
COOLIFY_API_TOKEN=请填本地 Coolify API Token
```

如果还要操作 Cloudflare DNS，可在同一文件补充：

```bash
CLOUDFLARE_API_TOKEN=请填本地 Cloudflare API Token
```

提交代码后的当前发布流程：

1. 本地验证变更：

```bash
./.venv/bin/pytest tests/composition/test_production_docker_assets.py tests/composition/test_coolify_deploy_script.py -q
cd apps/frontend_web && npm run build
```

2. 使用 `jj` 提交并推送 `master`。

3. 先读取 Coolify 当前状态：

```bash
./.venv/bin/python scripts/deploy_coolify_production.py --status-only
```

4. 触发生产重新部署并等待 `running:healthy`：

```bash
./.venv/bin/python scripts/deploy_coolify_production.py
```

5. 验证公网后端与前端入口：

```bash
curl -f https://api.quantpoly.com/health
curl -sS -D /tmp/quantpoly.headers -o /tmp/quantpoly.html https://quantpoly.com/
rg 'x-opennext|_next|/assets/index-|QuantPoly · 可解释' /tmp/quantpoly.headers /tmp/quantpoly.html
```

说明：

- Coolify v4 当前部署入口是 `GET /api/v1/deploy?uuid=...&force=false`。
- 不要用 `HEAD` 探测部署 endpoint；历史上 `HEAD` 也可能触发一次部署。
- 脚本会优先根据 Coolify 返回的 `deployment_uuid` 轮询部署记录，直到部署状态 `finished` 且 Application 回到 `running:healthy`。
- `--dry-run` 只打印将调用的 endpoint，不触发联网请求：

```bash
./.venv/bin/python scripts/deploy_coolify_production.py --dry-run
```

## 5.3 Cloudflare 前端入口切流

当前 `quantpoly.com` 与 `www.quantpoly.com` 的 DNS 记录已指向生产服务器：

- `quantpoly.com`：A `152.53.243.63`，proxied
- `www.quantpoly.com`：A `152.53.243.63`，proxied

`2026-05-01` 已在 Cloudflare Dashboard 中从旧 Worker `quantpoly-frontend` 删除以下路由：

- `quantpoly.com/*`
- `www.quantpoly.com/*`

删除后，公网验证应满足：

- 响应头不再出现 `x-powered-by: Next.js`
- 响应头不再出现 `x-opennext: 1`
- HTML 命中 Vite/TanStack 静态资源，例如 `/assets/index-*`

如果后续公网响应头再次出现：

- `x-powered-by: Next.js`
- `x-opennext: 1`
- HTML 内大量 `/_next/...`

说明请求仍被 Cloudflare Workers / Pages 的自定义域名或 route 在更高优先级接管，没有到达 Coolify origin。这种情况下不是“必须把新前端打包上传到 Cloudflare”，而是需要先选定托管模式：

1. 推荐模式：Coolify 托管前端，Cloudflare 只做 DNS / CDN / TLS 代理。
   - 移除或禁用 `quantpoly.com`、`www.quantpoly.com` 对应的 Workers route、Workers custom domain 或 Pages custom domain。
   - 保留 DNS A 记录指向 `152.53.243.63` 且 `proxied=true`。
   - Purge Cloudflare cache 后重新验证响应头和 HTML。
2. 备选模式：Cloudflare Pages / Workers 托管前端。
   - 需要另建 Cloudflare 构建/上传流程。
   - 后端仍走 `api.quantpoly.com`，同时要重新确认 `VITE_BACKEND_ORIGIN`、CORS 与 Cookie 策略。
   - 这会把当前“Coolify 全栈单 Compose”拆成前端 Cloudflare + 后端 Coolify，不是本手册默认路径。

当前本地 Cloudflare token 已验证可读取/更新 DNS，但读取 Workers / Pages API 与 purge cache API 仍会返回 `Authentication error`。如后续需要通过 API 自动审计或修改 Workers / Pages，需要提供具备 Workers / Pages 读取与编辑权限、Zone cache purge 权限的新 token，仍放在本地 `.local.env` / `.secret.env` 文件中，不提交。

不要为了绕开 Workers / Pages 接管而直接把根域名切成灰云直连，除非已确认 Traefik / Coolify origin 对 `quantpoly.com` 和 `www.quantpoly.com` 返回有效证书；否则浏览器会遇到 origin TLS 证书错误。

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

## 9. Coolify API Token 权限建议

建议使用只覆盖当前 Project / Environment / Application 的操作 token：

- 可读取 Application 状态
- 可触发 Application redeploy
- 可读取部署日志

不建议授予的权限：

- 全局删除资源权限
- 跨项目管理权限（除非你明确需要）
- 服务器 SSH / 密钥管理权限
