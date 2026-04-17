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
- 环境变量模板：`deploy/coolify/.env.fullstack.example`
- 密钥约束：`deploy/secrets/README.md`

## 4. 关键约束

- 任何真实密钥不得提交到 Git。
- `deploy/secrets/` 下真实文件必须使用 `.local.env` 或 `.secret.env` 后缀。
- 修改部署模板前，应先确认是否与 `docs/runbooks/fullstack-coolify-deployment-runbook.md` 的当前事实一致。
- 变更部署行为、环境变量语义或发布流程时，优先同步更新运行手册。

## 5. 常用入口

```bash
# 查看全栈部署手册
sed -n '1,220p' docs/runbooks/fullstack-coolify-deployment-runbook.md

# 查看 Coolify 环境变量模板
sed -n '1,220p' deploy/coolify/.env.fullstack.example
```

## 6. 关联文档

- 根级协作入口：`docs/guides/ai-collaboration.md`
- 文档总入口：`docs/README.md`
- 全栈部署手册：`docs/runbooks/fullstack-coolify-deployment-runbook.md`
