---
name: coolify-fullstack-cutover
description: Use when deploying a fullstack repository to Coolify and cutting over production traffic via Cloudflare with minimal downtime.
---

# Coolify 全栈切流技能

## 概览

用于将前后端统一部署到 Coolify，并通过 Cloudflare 完成生产流量切换。  
该技能强调两点：先恢复可用，再做清理；任何密钥只用环境变量注入，不写进文档与代码。

## 适用场景

- 需要把单仓库前后端（含数据库）部署到 Coolify。
- 需要将线上域名从旧服务切换到新服务。
- 需要通过 API 自动化执行部署与验证。

不适用：

- 仅本地开发环境。
- 已有成熟 CI/CD 且不允许直接调用平台 API。

## 前置检查

1. 仓库中存在可被 Coolify 直接读取的 Compose 文件（建议仓库根目录，如 `/docker-compose.coolify.yml`）。
2. 后端存在稳定健康检查端点（例如 `/health`）。
3. 已准备以下占位符变量：
   - `COOLIFY_BASE_URL`
   - `COOLIFY_API_TOKEN`
   - `PROJECT_UUID`
   - `SERVER_UUID`
   - `ENVIRONMENT_NAME`
   - `CF_API_TOKEN`
   - `CF_ZONE_ID`

## 执行流程

1. 发布代码到远端分支  
   - 先把 Dockerfile、Compose、运行手册推到远端默认分支。  
   - 避免本地已改、远端未推导致 Coolify 拉取失败。

2. 创建或更新 Coolify 应用  
   - 创建：`POST /api/v1/applications/public`  
   - 关键字段：`git_repository`、`git_branch`、`build_pack=dockercompose`、`docker_compose_location`
   - 更新：`PATCH /api/v1/applications/{app_uuid}`

3. 注入环境变量  
   - 应用场景：`PATCH /api/v1/applications/{app_uuid}/envs/bulk`  
   - 服务场景：`PATCH /api/v1/services/{service_uuid}/envs`（逐条）  
   - 至少包含：数据库密码、前端构建后端地址、后端 CORS、Cookie 安全项。

4. 触发部署  
   - `POST /api/v1/deploy`，请求体 `{ "uuid": "<resource_uuid>" }`

5. 轮询状态  
   - 部署状态：`GET /api/v1/deployments/{deployment_uuid}`  
   - 资源状态：`GET /api/v1/applications/{app_uuid}` 或 `GET /api/v1/resources`
   - 验收标准：外部 `https://api.<domain>/health` 返回 `200`。

6. Cloudflare 切流  
   - 更新 DNS 记录指向目标源站。  
   - 保持代理策略与证书策略一致。  
   - 切流后可选执行缓存清理（Purge）。

7. 冒烟与回归  
   - 后端：`/health`、鉴权接口、核心业务接口。  
   - 前端：首页加载、登录流程、关键页面跳转。  
   - Cookie：确认 `Secure`、`SameSite`、`Domain` 符合预期。

8. 清理  
   - 删除失败的临时资源，仅保留当前健康资源。  
   - 轮换本次会话暴露过的 Token。

## 常见问题

- 分支名错误（`main`/`master` 不一致）导致部署秒失败。
- Compose 中 `build.context` 与 Coolify 工作目录不匹配导致构建失败。
- 仅看平台状态 `running`，未做外部 URL 验证，导致“看起来正常但不可用”。
- 没有先推远端就触发部署，导致找不到 Compose 或 Dockerfile。

## 最小验证清单

- `GET /health` = `200`
- 登录成功并返回安全 Cookie
- 主域名页面返回新前端标识
- 旧无效健康路径返回预期错误（避免误判）
