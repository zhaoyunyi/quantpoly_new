# 部署目录（deploy）

## 1. 目标

本目录承载部署相关资产与本地密钥约定，当前重点包括：

- Coolify 全栈部署模板
- 部署环境变量示例
- 本地密钥文件约束

## 2. 目录约定

- `coolify/`：Coolify 用的 Compose 模板与环境变量示例
- `secrets/`：仅本地使用的密钥与令牌文件，不进入版本管理

## 3. 当前部署事实

- 全栈 Coolify 部署手册：`docs/runbooks/fullstack-coolify-deployment-runbook.md`
- 生产参考 Compose：`deploy/coolify/docker-compose.fullstack.yml`
- 本地浏览器级验证 override：`docker-compose.coolify.local.yml`
- 环境变量模板：`deploy/coolify/.env.fullstack.example`
- 密钥约束：`deploy/secrets/README.md`
- 截至 `2026-04-18`，前端构建链路已重新验证通过：
  - `cd apps/frontend_web && npm run build`
  - 干净环境 `npm ci && npm run build`
- 审计与收敛记录：`docs/migration/2026-04-18-doc-code-consistency-audit.md`

## 4. 关键约束

- 任何真实密钥不得提交到 Git。
- `deploy/secrets/` 下真实文件必须使用 `.local.env` 或 `.secret.env` 后缀。
- 修改部署模板前，应先确认是否与 `docs/runbooks/fullstack-coolify-deployment-runbook.md` 的当前事实一致。
- 如果变更涉及前端镜像构建，应先确认 `apps/frontend_web` 的 npm 基线没有再次漂移。
- 如果需要本地做接近生产的 Compose 联调，优先复用 `docker-compose.coolify.local.yml`，不要直接改生产 Compose。
- 变更部署行为、环境变量语义或发布流程时，优先同步更新运行手册。

## 5. 常用入口

```bash
# 查看全栈部署手册
sed -n '1,220p' docs/runbooks/fullstack-coolify-deployment-runbook.md

# 查看 Coolify 环境变量模板
sed -n '1,220p' deploy/coolify/.env.fullstack.example

# 一键执行本地 Coolify Compose + Playwright 验证
./.venv/bin/python scripts/verify_coolify_local_stack.py

# GitHub Actions 工作流入口
sed -n '1,220p' .github/workflows/verify-coolify-local-stack.yml
```

## 6. 关联文档

- 根级协作入口：`docs/guides/ai-collaboration.md`
- 文档总入口：`docs/README.md`
- 全栈部署手册：`docs/runbooks/fullstack-coolify-deployment-runbook.md`
