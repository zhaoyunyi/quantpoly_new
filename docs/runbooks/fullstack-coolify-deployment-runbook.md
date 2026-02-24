# 全栈 Coolify 部署手册（frontend + backend + postgres）

> 目标：在 Coolify 上以单个 Docker Compose 资源部署新前端与新后端，并覆盖线上流量。

## 1. 对应部署资产

- Compose：`deploy/coolify/docker-compose.fullstack.yml`
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
3. `Compose Path` 填：`deploy/coolify/docker-compose.fullstack.yml`。
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

1. 点击 `Deploy`。
2. 等待三个服务都变为 `Healthy`。
3. 验证：

```bash
curl -f https://api.example.com/health
curl -I https://app.example.com/
```

4. 登录一次，确认响应头 `Set-Cookie` 带 `Secure`（生产环境必须）。

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
