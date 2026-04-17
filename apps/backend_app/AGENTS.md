# 后端组合入口（backend_app）

## 1. 目标

本目录承载 QuantPoly 后端的 **Composition Root**，负责：

- 读取环境与运行配置
- 组装各领域库的 repository / service / router
- 安装全局中间件、异常处理、CORS 与观测能力
- 提供组合配置解析 CLI

这里不是业务规则的主要落点；业务能力应优先沉到 `libs/`。

## 2. 文件职责

- `app.py`：FastAPI 应用工厂 `create_app`
- `router_registry.py`：上下文装配、路由注册、依赖构造、基础指标
- `settings.py`：组合入口配置模型与环境变量归一化
- `cli.py`：组合配置解析 CLI（`resolve-settings`）

## 3. 目录边界

- 业务上下文实现位于 `libs/`
- 本目录只负责“接线”和“装配”，不要把领域逻辑继续堆在这里
- 新增能力时，优先先补对应 `libs/<context>/`，再回到这里注册

## 4. 关键约束

- 遵循 `spec/ProgramSpec.md`：Library-First、CLI Mandate、Test-First
- 遵循 `spec/DDDSpec.md`：组合入口不承载领域逻辑
- 当前主存储后端为 `postgres`，本地/测试允许 `memory`
- 用户系统主逻辑由后端承担，不得把认证判断下沉回前端

## 5. 常用命令

```bash
# 启动后端
uvicorn apps.backend_app:create_app --factory --reload --port 8000

# 查看组合配置解析 CLI
./.venv/bin/python -m apps.backend_app.cli resolve-settings --help

# 解析组合配置（stdin）
echo '{}' | ./.venv/bin/python -m apps.backend_app.cli resolve-settings

# 冒烟
python3 scripts/smoke_backend_composition.py --base-url http://127.0.0.1:8000
```

## 6. 关联文档

- 当前实现事实：`docs/migration/2026-02-13-backend-current-state.md`
- 运行手册：`docs/runbooks/backend-operations-runbook.md`
- 门禁手册：`docs/gates/backend-gate-handbook.md`
- 根级协作入口：`docs/guides/ai-collaboration.md`
